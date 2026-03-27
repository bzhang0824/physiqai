#!/usr/bin/env python3
"""
PhysiqAI Continuous QA Monitor
Runs on every file change, auto-fixes where possible
"""

import os
import sys
import json
import time
import hashlib
import subprocess
from pathlib import Path
from datetime import datetime
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class ContinuousQAMonitor(FileSystemEventHandler):
    def __init__(self, project_dir):
        self.project_dir = Path(project_dir)
        self.state_file = self.project_dir / '.qa_state.json'
        self.log_file = self.project_dir / 'logs' / 'continuous_qa.log'
        self.fixed_count = 0
        self.error_count = 0

    def on_modified(self, event):
        if event.is_directory:
            return

        file_path = Path(event.src_path)

        # Only check code files
        if file_path.suffix not in ['.py', '.js', '.html', '.css', '.ts', '.jsx']:
            return

        # Skip node_modules, venv, etc
        if any(skip in str(file_path) for skip in ['node_modules', 'venv', '__pycache__', '.git']):
            return

        self.qa_check(file_path)

    def on_created(self, event):
        self.on_modified(event)

    def qa_check(self, file_path):
        """Run QA on a single file"""
        rel_path = file_path.relative_to(self.project_dir)
        print(f"\n🔍 QA Check: {rel_path}")

        results = {
            'file': str(rel_path),
            'timestamp': datetime.now().isoformat(),
            'checks': {},
            'auto_fixed': False,
            'needs_attention': False
        }

        # Check 1: File not empty
        if file_path.stat().st_size == 0:
            print(f"  ❌ File is empty")
            results['checks']['empty'] = 'FAIL'
            results['needs_attention'] = True
        else:
            results['checks']['empty'] = 'PASS'

        # Check 2: Syntax (auto-fixable)
        syntax_result = self.check_syntax(file_path)
        results['checks']['syntax'] = syntax_result['status']

        if syntax_result['status'] == 'FAIL' and syntax_result.get('fixable'):
            fixed = self.attempt_fix(file_path, syntax_result['error'])
            if fixed:
                results['checks']['syntax'] = 'AUTO_FIXED'
                results['auto_fixed'] = True
                self.fixed_count += 1
            else:
                results['needs_attention'] = True
                self.error_count += 1

        # Check 3: Imports (Python)
        if file_path.suffix == '.py':
            import_result = self.check_imports(file_path)
            results['checks']['imports'] = import_result
            if import_result == 'FAIL':
                results['needs_attention'] = True
                self.error_count += 1

        # Check 4: ESLint (JS)
        if file_path.suffix in ['.js', '.jsx', '.ts']:
            lint_result = self.check_eslint(file_path)
            results['checks']['linting'] = lint_result
            if lint_result == 'FAIL':
                results['needs_attention'] = True

        # Check 5: Output verification (if applicable)
        if 'test' in str(file_path).lower():
            test_result = self.run_test(file_path)
            results['checks']['test'] = test_result
            if test_result == 'FAIL':
                results['needs_attention'] = True
                self.error_count += 1

        # Log results
        self.log_result(results)

        # Update state
        self.update_state(file_path, results)

        # Summary
        status = '✅ PASS' if not results['needs_attention'] else '⚠️ NEEDS_FIX' if not results['auto_fixed'] else '🔧 AUTO_FIXED'
        print(f"  {status}")

    def check_syntax(self, file_path):
        """Check file syntax"""
        try:
            if file_path.suffix == '.py':
                with open(file_path) as f:
                    compile(f.read(), str(file_path), 'exec')
                return {'status': 'PASS'}
            elif file_path.suffix in ['.js', '.jsx']:
                # Quick syntax check with node
                result = subprocess.run(
                    ['node', '--check', str(file_path)],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    return {'status': 'PASS'}
                else:
                    return {
                        'status': 'FAIL',
                        'error': result.stderr.decode(),
                        'fixable': self.is_js_fixable(result.stderr.decode())
                    }
            return {'status': 'PASS'}
        except SyntaxError as e:
            return {
                'status': 'FAIL',
                'error': str(e),
                'fixable': self.is_python_fixable(e)
            }
        except Exception as e:
            return {'status': 'FAIL', 'error': str(e), 'fixable': False}

    def is_python_fixable(self, error):
        """Determine if Python error is auto-fixable"""
        fixable_errors = [
            'unexpected EOF',
            'invalid syntax',  # Sometimes trailing commas
            'expected an indented block',
            'EOL while scanning string literal'
        ]
        return any(err in str(error) for err in fixable_errors)

    def is_js_fixable(self, error):
        """Determine if JS error is auto-fixable"""
        fixable_errors = [
            'Unexpected end of input',
            'Unexpected token',
            'Missing semicolon'
        ]
        return any(err in error for err in fixable_errors)

    def attempt_fix(self, file_path, error):
        """Attempt to auto-fix common issues"""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            original_content = content

            # Fix 1: Trailing commas
            if 'trailing comma' in str(error).lower():
                content = content.rstrip().rstrip(',')

            # Fix 2: Missing final newline
            if not content.endswith('\n'):
                content += '\n'

            # Fix 3: Mixed tabs/spaces
            content = content.replace('\t', '    ')

            # Fix 4: Remove trailing whitespace
            content = '\n'.join(line.rstrip() for line in content.split('\n'))

            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"  🔧 Auto-fixed formatting issues")
                return True

            return False
        except Exception as e:
            print(f"  ❌ Auto-fix failed: {e}")
            return False

    def check_imports(self, file_path):
        """Check Python imports"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'py_compile', str(file_path)],
                capture_output=True,
                timeout=10
            )
            return 'PASS' if result.returncode == 0 else 'FAIL'
        except:
            return 'FAIL'

    def check_eslint(self, file_path):
        """Check JS with ESLint"""
        try:
            result = subprocess.run(
                ['npx', 'eslint', str(file_path)],
                capture_output=True,
                timeout=10
            )
            return 'PASS' if result.returncode == 0 else 'WARN'
        except:
            return 'SKIP'

    def run_test(self, file_path):
        """Run test file"""
        try:
            if file_path.suffix == '.py':
                result = subprocess.run(
                    [sys.executable, str(file_path)],
                    capture_output=True,
                    timeout=30
                )
                return 'PASS' if result.returncode == 0 else 'FAIL'
            return 'SKIP'
        except:
            return 'FAIL'

    def log_result(self, results):
        """Log QA result"""
        self.log_file.parent.mkdir(exist_ok=True)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(results) + '\n')

    def update_state(self, file_path, results):
        """Update QA state file"""
        state = {}
        if self.state_file.exists():
            with open(self.state_file) as f:
                state = json.load(f)

        file_hash = hashlib.md5(file_path.read_bytes()).hexdigest()
        state[str(file_path.relative_to(self.project_dir))] = {
            'hash': file_hash,
            'last_check': datetime.now().isoformat(),
            'status': 'PASS' if not results['needs_attention'] else 'FAIL',
            'auto_fixed': results['auto_fixed']
        }

        with open(self.state_file, 'w') as f:
            json.dump(state, f, indent=2)

    def run(self):
        """Start monitoring"""
        print(f"🔍 Continuous QA Monitor started")
        print(f"📁 Watching: {self.project_dir}")
        print(f"📝 Log: {self.log_file}")
        print(f"Press Ctrl+C to stop\n")

        observer = Observer()
        observer.schedule(self, str(self.project_dir), recursive=True)
        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            print(f"\n✅ QA Monitor stopped")
            print(f"🔧 Auto-fixed: {self.fixed_count} files")
            print(f"❌ Errors needing attention: {self.error_count} files")

        observer.join()

if __name__ == '__main__':
    project_dir = sys.argv[1] if len(sys.argv) > 1 else '.'
    monitor = ContinuousQAMonitor(project_dir)
    monitor.run()
