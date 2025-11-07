#!/usr/bin/env python3
"""
Real scoring engine for benchmark tasks.

Implements actual validation logic for different task types rather than
placeholder/mock scoring.
"""

import os
import re
import ast
import json
import time
import subprocess
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class ScoreResult:
    """Result of scoring a single task."""
    task_id: str
    score: float  # 0.0 - 1.0
    max_score: float
    details: Dict[str, Any]
    errors: List[str]
    execution_time: float


class TaskScorer(ABC):
    """Abstract base class for task-specific scorers."""
    
    @abstractmethod
    def score(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score a task after patch application."""
        pass


class CrossFileReasoningScorer(TaskScorer):
    """Scorer for cross-file reasoning tasks."""
    
    def score(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score cross-file reasoning by checking if agent found correct call path."""
        start_time = time.time()
        task_id = task['task_id']
        
        errors = []
        details = {
            "expected_path_found": False,
            "implementation_file_found": False,
            "call_chain_accuracy": 0.0,
            "agent_output_format": "unknown"
        }
        
        try:
            # Load ground truth
            ground_truth_file = task.get('ground_truth', '')
            if not ground_truth_file or not os.path.exists(ground_truth_file):
                errors.append(f"Ground truth file not found: {ground_truth_file}")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
            
            expected_path = ground_truth.get('expected_call_path', [])
            expected_file = ground_truth.get('expected_implementation_file', '')
            expected_lines = ground_truth.get('expected_line_range', [])
            
            if not expected_path:
                errors.append("No expected call path in ground truth")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            # Look for agent's output - could be in patch comments, separate file, or git commit message
            agent_output = self._extract_agent_reasoning(repo_path)
            
            if not agent_output:
                details["agent_output_format"] = "none_found"
                score = 0.0
            else:
                details["agent_output_format"] = "text_found"
                score = self._analyze_reasoning_output(agent_output, expected_path, expected_file, expected_lines, details)
            
        except Exception as e:
            errors.append(f"Scoring error: {e}")
            score = 0.0
        
        execution_time = time.time() - start_time
        
        return ScoreResult(
            task_id=task_id,
            score=score,
            max_score=1.0,
            details=details,
            errors=errors,
            execution_time=execution_time
        )
    
    def _extract_agent_reasoning(self, repo_path: str) -> str:
        """Extract agent's reasoning output from various sources."""
        reasoning_text = ""
        
        # Check for reasoning files
        for filename in ['REASONING.md', 'reasoning.txt', 'analysis.md', 'SOLUTION.md']:
            path = os.path.join(repo_path, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    reasoning_text += f.read() + "\n"
        
        # Check git commit messages
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-n', '5'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                reasoning_text += result.stdout + "\n"
        except:
            pass
        
        return reasoning_text
    
    def _analyze_reasoning_output(self, output: str, expected_path: List[str], 
                                 expected_file: str, expected_lines: List[int],
                                 details: Dict[str, Any]) -> float:
        """Analyze agent's reasoning text for correctness."""
        score = 0.0
        output_lower = output.lower()
        
        # Check if implementation file was identified (25% of score)
        if expected_file:
            file_basename = os.path.basename(expected_file)
            if file_basename.lower() in output_lower or expected_file in output:
                details["implementation_file_found"] = True
                score += 0.25
        
        # Check call path accuracy (50% of score)
        path_score = 0.0
        for i, path_element in enumerate(expected_path):
            # Look for file names and function names in the path
            if '::' in path_element or '->' in path_element or '.' in path_element:
                parts = re.split(r'[:>\.]', path_element)
                for part in parts:
                    if part.strip() and part.strip().lower() in output_lower:
                        path_score += 1.0 / len(expected_path)
                        break
            elif path_element.lower() in output_lower:
                path_score += 1.0 / len(expected_path)
        
        details["call_chain_accuracy"] = path_score
        score += path_score * 0.5
        
        # Check if correct analysis method was used (25% of score)
        analysis_keywords = ['call', 'trace', 'path', 'flow', 'implementation', 'function', 'method']
        analysis_score = sum(1 for keyword in analysis_keywords if keyword in output_lower) / len(analysis_keywords)
        score += min(analysis_score, 1.0) * 0.25
        
        details["expected_path_found"] = score > 0.5
        
        return min(score, 1.0)
    
    def _error_result(self, task_id: str, errors: List[str], execution_time: float) -> ScoreResult:
        """Return error result."""
        return ScoreResult(
            task_id=task_id,
            score=0.0,
            max_score=1.0,
            details={"error": True},
            errors=errors,
            execution_time=execution_time
        )


class RefactorRenameScorer(TaskScorer):
    """Scorer for refactor/rename tasks."""
    
    def score(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score refactor/rename by checking if all references were updated."""
        start_time = time.time()
        task_id = task['task_id']
        
        errors = []
        details = {
            "files_checked": 0,
            "correctly_modified": 0,
            "missed_references": 0,
            "false_positives": 0,
            "compilation_success": False
        }
        
        try:
            if not patch_applied:
                return self._error_result(task_id, ["No patch was applied"], time.time() - start_time)
            
            # Load ground truth
            ground_truth_file = task.get('ground_truth', '')
            if not ground_truth_file or not os.path.exists(ground_truth_file):
                errors.append(f"Ground truth file not found: {ground_truth_file}")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
            
            old_symbol = task.get('symbol_to_rename', '')
            new_symbol = task.get('new_name', '')
            
            if not old_symbol or not new_symbol:
                errors.append("Missing symbol names in task definition")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            # Check each expected file modification
            expected_changes = ground_truth.get('expected_changes', [])
            details["files_checked"] = len(expected_changes)
            
            for change in expected_changes:
                file_path = change['file']
                if self._check_file_rename(file_path, old_symbol, new_symbol, change):
                    details["correctly_modified"] += 1
                else:
                    details["missed_references"] += 1
            
            # Check for false positives (incorrect renames)
            false_positives = self._check_false_positives(repo_path, old_symbol, new_symbol)
            details["false_positives"] = false_positives
            
            # Try compilation if possible
            compilation_ok = self._check_compilation(repo_path)
            details["compilation_success"] = compilation_ok
            
            # Calculate score
            accuracy = details["correctly_modified"] / max(details["files_checked"], 1)
            false_positive_penalty = min(details["false_positives"] * 0.1, 0.3)
            compilation_bonus = 0.1 if compilation_ok else 0.0
            
            score = max(0.0, accuracy - false_positive_penalty + compilation_bonus)
            
        except Exception as e:
            errors.append(f"Scoring error: {e}")
            score = 0.0
        
        execution_time = time.time() - start_time
        
        return ScoreResult(
            task_id=task_id,
            score=min(score, 1.0),
            max_score=1.0,
            details=details,
            errors=errors,
            execution_time=execution_time
        )
    
    def _check_file_rename(self, file_path: str, old_symbol: str, new_symbol: str, 
                          expected_change: Dict[str, Any]) -> bool:
        """Check if a file was correctly modified."""
        try:
            if not os.path.exists(file_path):
                return False
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Check if old symbol is gone (or significantly reduced)
            old_count = len(re.findall(rf'\b{re.escape(old_symbol)}\b', content))
            
            # Check if new symbol appears
            new_count = len(re.findall(rf'\b{re.escape(new_symbol)}\b', content))
            
            # For a good rename, old symbol should be rare/gone and new symbol should appear
            return old_count <= 2 and new_count >= 1
            
        except Exception:
            return False
    
    def _check_false_positives(self, repo_path: str, old_symbol: str, new_symbol: str) -> int:
        """Check for incorrect renames (false positives)."""
        false_positives = 0
        
        # Look for common false positive patterns
        try:
            # Use ripgrep or grep to find potential issues
            result = subprocess.run(
                ['grep', '-r', '--include=*.go', '--include=*.py', '--include=*.cpp', 
                 new_symbol, repo_path],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.split('\n')
                # Heuristic: if new symbol appears in comments or strings, might be false positive
                for line in lines[:50]:  # Check first 50 matches
                    if '//' in line or '#' in line or '"' in line or "'" in line:
                        false_positives += 1
                        
        except:
            pass
        
        return min(false_positives, 10)  # Cap at 10
    
    def _check_compilation(self, repo_path: str) -> bool:
        """Check if code still compiles after rename."""
        try:
            # Try Go compilation
            if any(Path(repo_path).rglob("*.go")):
                result = subprocess.run(
                    ['go', 'build', './...'],
                    cwd=repo_path,
                    capture_output=True,
                    timeout=30
                )
                return result.returncode == 0
            
            # Try Python syntax check on a sample
            py_files = list(Path(repo_path).rglob("*.py"))[:5]
            for py_file in py_files:
                try:
                    with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                        ast.parse(f.read())
                except SyntaxError:
                    return False
            
            return True
            
        except:
            return False
    
    def _error_result(self, task_id: str, errors: List[str], execution_time: float) -> ScoreResult:
        """Return error result."""
        return ScoreResult(
            task_id=task_id,
            score=0.0,
            max_score=1.0,
            details={"error": True},
            errors=errors,
            execution_time=execution_time
        )


class APIUpgradeScorer(TaskScorer):
    """Scorer for API upgrade tasks."""
    
    def score(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score API upgrade by checking callsite migrations."""
        start_time = time.time()
        task_id = task['task_id']
        
        errors = []
        details = {
            "total_callsites": 0,
            "expected_upgrades": 0,
            "actual_upgrades": 0,
            "upgrade_accuracy": 0.0,
            "preserved_legacy": 0
        }
        
        try:
            if not patch_applied:
                return self._error_result(task_id, ["No patch was applied"], time.time() - start_time)
            
            # Load ground truth
            ground_truth_file = task.get('ground_truth', '')
            if not ground_truth_file or not os.path.exists(ground_truth_file):
                errors.append(f"Ground truth file not found: {ground_truth_file}")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
            
            old_api = task.get('old_api', '')
            new_api = task.get('new_api', '')
            
            if not old_api or not new_api:
                errors.append("Missing API definitions in task")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            # Extract function names from API signatures
            old_func = self._extract_function_name(old_api)
            new_func = self._extract_function_name(new_api)
            
            if not old_func or not new_func:
                errors.append("Could not extract function names from API signatures")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            # Check callsite upgrades
            callsites = ground_truth.get('callsites', [])
            details["total_callsites"] = len(callsites)
            
            expected_upgrades = sum(1 for cs in callsites if cs.get('needs_upgrade', False))
            details["expected_upgrades"] = expected_upgrades
            
            actual_upgrades = 0
            preserved_legacy = 0
            
            for callsite in callsites:
                file_path = callsite['file']
                needs_upgrade = callsite.get('needs_upgrade', False)
                
                if not os.path.exists(file_path):
                    continue
                
                upgrade_found = self._check_callsite_upgrade(file_path, old_func, new_func)
                
                if needs_upgrade and upgrade_found:
                    actual_upgrades += 1
                elif not needs_upgrade and not upgrade_found:
                    preserved_legacy += 1
            
            details["actual_upgrades"] = actual_upgrades
            details["preserved_legacy"] = preserved_legacy
            
            # Calculate score
            upgrade_accuracy = actual_upgrades / max(expected_upgrades, 1)
            legacy_accuracy = preserved_legacy / max(len(callsites) - expected_upgrades, 1)
            
            details["upgrade_accuracy"] = upgrade_accuracy
            score = (upgrade_accuracy * 0.7) + (legacy_accuracy * 0.3)
            
        except Exception as e:
            errors.append(f"Scoring error: {e}")
            score = 0.0
        
        execution_time = time.time() - start_time
        
        return ScoreResult(
            task_id=task_id,
            score=min(score, 1.0),
            max_score=1.0,
            details=details,
            errors=errors,
            execution_time=execution_time
        )
    
    def _extract_function_name(self, api_signature: str) -> str:
        """Extract function name from API signature."""
        # Handle patterns like "FooMethod(param1, param2)" -> "FooMethod"
        match = re.search(r'(\w+)\s*\(', api_signature)
        return match.group(1) if match else ""
    
    def _check_callsite_upgrade(self, file_path: str, old_func: str, new_func: str) -> bool:
        """Check if a callsite was upgraded from old to new API."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            # Count occurrences
            old_count = len(re.findall(rf'\b{re.escape(old_func)}\s*\(', content))
            new_count = len(re.findall(rf'\b{re.escape(new_func)}\s*\(', content))
            
            # Upgrade happened if old is reduced and new is present
            return old_count == 0 and new_count > 0
            
        except Exception:
            return False
    
    def _error_result(self, task_id: str, errors: List[str], execution_time: float) -> ScoreResult:
        """Return error result."""
        return ScoreResult(
            task_id=task_id,
            score=0.0,
            max_score=1.0,
            details={"error": True},
            errors=errors,
            execution_time=execution_time
        )


class BugLocalizationScorer(TaskScorer):
    """Scorer for bug localization tasks."""
    
    def score(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score bug localization by checking if correct file/lines were identified."""
        start_time = time.time()
        task_id = task['task_id']
        
        errors = []
        details = {
            "correct_file": False,
            "correct_line_range": False,
            "fix_applied": False,
            "file_score": 0.0,
            "location_score": 0.0,
            "fix_score": 0.0
        }
        
        try:
            # Load ground truth
            ground_truth_file = task.get('ground_truth', '')
            if not ground_truth_file or not os.path.exists(ground_truth_file):
                errors.append(f"Ground truth file not found: {ground_truth_file}")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            with open(ground_truth_file, 'r') as f:
                ground_truth = json.load(f)
            
            bug_location = ground_truth.get('bug_location', {})
            expected_file = bug_location.get('file', '')
            expected_lines = bug_location.get('line_range', [])
            
            if not expected_file:
                errors.append("No expected bug file in ground truth")
                return self._error_result(task_id, errors, time.time() - start_time)
            
            # Look for agent's analysis
            analysis = self._extract_bug_analysis(repo_path)
            
            # Check file identification (40% of score)
            if expected_file in analysis or os.path.basename(expected_file) in analysis:
                details["correct_file"] = True
                details["file_score"] = 1.0
            
            # Check line range accuracy (30% of score)  
            if expected_lines and len(expected_lines) >= 2:
                line_score = self._check_line_accuracy(analysis, expected_lines)
                details["location_score"] = line_score
                details["correct_line_range"] = line_score > 0.5
            
            # Check if fix was applied (30% of score)
            if patch_applied:
                fix_applied = self._check_bug_fix(expected_file, expected_lines)
                details["fix_applied"] = fix_applied
                details["fix_score"] = 1.0 if fix_applied else 0.0
            
            # Calculate total score
            score = (details["file_score"] * 0.4 + 
                    details["location_score"] * 0.3 + 
                    details["fix_score"] * 0.3)
            
        except Exception as e:
            errors.append(f"Scoring error: {e}")
            score = 0.0
        
        execution_time = time.time() - start_time
        
        return ScoreResult(
            task_id=task_id,
            score=min(score, 1.0),
            max_score=1.0,
            details=details,
            errors=errors,
            execution_time=execution_time
        )
    
    def _extract_bug_analysis(self, repo_path: str) -> str:
        """Extract agent's bug analysis."""
        analysis_text = ""
        
        # Check for analysis files
        for filename in ['BUG_ANALYSIS.md', 'bug_report.txt', 'DIAGNOSIS.md']:
            path = os.path.join(repo_path, filename)
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                    analysis_text += f.read() + "\n"
        
        # Check commit messages
        try:
            result = subprocess.run(
                ['git', 'log', '--oneline', '-n', '3'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                analysis_text += result.stdout + "\n"
        except:
            pass
        
        return analysis_text
    
    def _check_line_accuracy(self, analysis: str, expected_lines: List[int]) -> float:
        """Check if correct line numbers were identified."""
        if len(expected_lines) < 2:
            return 0.0
        
        start_line, end_line = expected_lines[0], expected_lines[1]
        
        # Look for line numbers in analysis
        line_numbers = re.findall(r'\b(\d+)\b', analysis)
        found_numbers = [int(num) for num in line_numbers if num.isdigit()]
        
        # Check if any found numbers are in the expected range
        for num in found_numbers:
            if start_line - 5 <= num <= end_line + 5:  # ±5 lines tolerance
                if start_line - 2 <= num <= end_line + 2:  # ±2 lines = full score
                    return 1.0
                else:  # ±5 lines = partial score
                    return 0.75
        
        return 0.0
    
    def _check_bug_fix(self, expected_file: str, expected_lines: List[int]) -> bool:
        """Check if the bug appears to be fixed."""
        if not os.path.exists(expected_file):
            return False
        
        try:
            with open(expected_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not expected_lines or len(expected_lines) < 2:
                return False
            
            start_idx = max(0, expected_lines[0] - 1)
            end_idx = min(len(lines), expected_lines[1])
            
            # Look for fix patterns in the target lines
            target_lines = ''.join(lines[start_idx:end_idx]).lower()
            
            # Common fix indicators
            fix_patterns = [
                'if.*null', 'null.*check', '!= null', '== null',
                'try.*catch', 'error.*handle', 'validate',
                'bounds.*check', 'len.*check', 'size.*check'
            ]
            
            return any(re.search(pattern, target_lines) for pattern in fix_patterns)
            
        except Exception:
            return False
    
    def _error_result(self, task_id: str, errors: List[str], execution_time: float) -> ScoreResult:
        """Return error result."""
        return ScoreResult(
            task_id=task_id,
            score=0.0,
            max_score=1.0,
            details={"error": True},
            errors=errors,
            execution_time=execution_time
        )


class ScoringEngine:
    """Main scoring engine that coordinates all task scorers."""
    
    def __init__(self):
        self.scorers = {
            'cross_file_reasoning': CrossFileReasoningScorer(),
            'refactor_rename': RefactorRenameScorer(),
            'api_upgrade': APIUpgradeScorer(), 
            'bug_localization': BugLocalizationScorer()
        }
    
    def score_task(self, task: Dict[str, Any], repo_path: str, patch_applied: bool) -> ScoreResult:
        """Score a single task."""
        task_type = task.get('type', '')
        
        if task_type not in self.scorers:
            return ScoreResult(
                task_id=task.get('task_id', 'unknown'),
                score=0.0,
                max_score=1.0,
                details={"error": f"Unknown task type: {task_type}"},
                errors=[f"No scorer for task type: {task_type}"],
                execution_time=0.0
            )
        
        scorer = self.scorers[task_type]
        return scorer.score(task, repo_path, patch_applied)
    
    def score_all_tasks(self, tasks: List[Dict[str, Any]], repo_path: str, 
                       patch_applied: bool) -> List[ScoreResult]:
        """Score all tasks and return results."""
        results = []
        
        for task in tasks:
            try:
                result = self.score_task(task, repo_path, patch_applied)
                results.append(result)
                logger.info(f"Scored {task.get('task_id', 'unknown')}: {result.score:.3f}")
            except Exception as e:
                logger.error(f"Failed to score task {task.get('task_id', 'unknown')}: {e}")
                results.append(ScoreResult(
                    task_id=task.get('task_id', 'unknown'),
                    score=0.0,
                    max_score=1.0,
                    details={"error": str(e)},
                    errors=[str(e)],
                    execution_time=0.0
                ))
        
        return results


def main():
    """Test the scoring engine."""
    print("Scoring engine loaded successfully!")


if __name__ == "__main__":
    main()
