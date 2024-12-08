import requests
import json
import time
import argparse
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
import sys
import os
from pathlib import Path
from urllib.parse import urljoin
import colorama
from colorama import Fore, Back, Style

# Initialize colorama
colorama.init()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutomationAPITester:
    def __init__(self, base_url: str = "http://localhost:1234"):
        self.base_url = base_url.rstrip('/')
        self.api_base = f"{self.base_url}/api"
        self.session = requests.Session()
        self.test_results = []

    def _make_request(self,
                      method: str,
                      endpoint: str,
                      params: Optional[Dict] = None,
                      json_data: Optional[Dict] = None,
                      timeout: int = 30) -> Dict[str, Any]:
        """Make HTTP request with error handling"""
        url = f"{self.api_base}/{endpoint.lstrip('/')}"
        try:
            logger.info(f"Making {method} request to: {url}")
            if json_data:
                logger.info(f"Request data: {json_data}")

            response = self.session.request(
                method=method,
                url=url,
                params=params,
                json=json_data,
                timeout=timeout
            )

            if response.content:
                try:
                    data = response.json()
                except json.JSONDecodeError:
                    data = {'error': 'Invalid JSON response', 'raw': response.text}
            else:
                data = None

            return {
                'status_code': response.status_code,
                'data': data,
                'success': response.ok,
                'headers': dict(response.headers)
            }
        except requests.exceptions.Timeout:
            logger.error(f"Request timeout: {url}")
            return {
                'status_code': 408,
                'data': {'error': 'Request timeout'},
                'success': False
            }
        except requests.exceptions.ConnectionError:
            logger.error(f"Connection error: {url}")
            return {
                'status_code': 503,
                'data': {'error': 'Connection error - Is the server running?'},
                'success': False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            return {
                'status_code': 500,
                'data': {'error': str(e)},
                'success': False
            }

    def print_response(self, test_name: str, response: Dict[str, Any], save_to_file: bool = False):
        """Pretty print response with color coding"""
        is_success = response['success']
        color = Fore.GREEN if is_success else Fore.RED

        output = [
            f"\n{color}=== {test_name} ==={Style.RESET_ALL}",
            f"Status Code: {response['status_code']}",
        ]

        # Add headers if verbose
        if logger.level == logging.DEBUG:
            output.append("\nHeaders:")
            for header, value in response.get('headers', {}).items():
                output.append(f"{header}: {value}")

        # Add response data
        output.append("\nResponse Data:")
        if isinstance(response['data'], dict):
            output.append(json.dumps(response['data'], indent=2))
        else:
            output.append(str(response['data']))

        output.append(f"{color}{'=' * (len(test_name) + 8)}{Style.RESET_ALL}\n")

        # Print to console
        print('\n'.join(output))

        # Save to file if requested
        if save_to_file:
            self._save_to_file(test_name, output)

        # Store test result
        self.test_results.append({
            'name': test_name,
            'success': is_success,
            'status_code': response['status_code'],
            'timestamp': datetime.now().isoformat()
        })

    def _save_to_file(self, test_name: str, content: List[str]):
        """Save test output to file"""
        reports_dir = Path('test_reports')
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{test_name.replace(' ', '_')}_{timestamp}.txt"

        with open(reports_dir / filename, 'w', encoding='utf-8') as f:
            f.write('\n'.join(content))

    def test_list_commands(self, command_type: Optional[str] = None, save_output: bool = False):
        """Test getting available commands"""
        params = {'type': command_type} if command_type else {}
        response = self._make_request('GET', 'commands/list/', params=params)
        self.print_response(f"List Commands (type={command_type})", response, save_output)
        return response

    def test_execute_command(self,
                             command: str,
                             params: Optional[Dict] = None,
                             timeout: int = 10,
                             save_output: bool = False):
        """Test executing a command"""
        data = {
            "command": command,
            "params": params or {},
            "timeout": timeout
        }
        response = self._make_request('POST', 'commands/execute/', json_data=data)
        self.print_response(f"Execute Command: {command}", response, save_output)
        return response

    def test_command_history(self,
                             command: Optional[str] = None,
                             limit: int = 10,
                             status: Optional[str] = None,
                             save_output: bool = False):
        """Test getting command history"""
        params = {'limit': limit}
        if command:
            params['command'] = command
        if status:
            params['status'] = status

        response = self._make_request('GET', 'commands/history/', params=params)
        self.print_response(
            f"Command History (command={command}, status={status})",
            response,
            save_output
        )
        return response

    def test_storage_data(self,
                          storage_type: Optional[str] = None,
                          timeout: int = 10,
                          keys: Optional[list] = None,
                          save_output: bool = False):
        """Test getting storage data"""
        params = {'timeout': timeout}
        if storage_type:
            params['type'] = storage_type
        if keys:
            params['keys'] = ','.join(keys)

        response = self._make_request('GET', 'storage/data/', params=params)
        self.print_response(f"Storage Data (type={storage_type})", response, save_output)
        return response

    def test_basic_dom_commands(self, save_output: bool = False):
        """Test basic DOM-related commands"""
        print(f"\n{Fore.CYAN}Running Basic DOM Commands Tests...{Style.RESET_ALL}")

        results = {
            'title': self.test_execute_command("getTitle", save_output=save_output),
            'url': self.test_execute_command("getUrl", save_output=save_output),
            'metadata': self.test_execute_command("getMetadata", save_output=save_output),
            'dom_stats': self.test_execute_command("getDOMStats", save_output=save_output),
            'links': self.test_execute_command("getLinks", save_output=save_output)
        }
        return results

    def test_storage_commands(self, save_output: bool = False):
        """Test storage-related commands"""
        print(f"\n{Fore.CYAN}Running Storage Commands Tests...{Style.RESET_ALL}")

        results = {
            'all_storage': self.test_storage_data(save_output=save_output),
            'cookies': self.test_storage_data('cookies', save_output=save_output),
            'localStorage': self.test_storage_data('localStorage', save_output=save_output),
            'sessionStorage': self.test_storage_data('sessionStorage', save_output=save_output)
        }
        return results

    def test_error_cases(self, save_output: bool = False):
        """Test various error cases"""
        print(f"\n{Fore.CYAN}Running Error Case Tests...{Style.RESET_ALL}")

        results = {
            'invalid_command': self.test_execute_command(
                "invalid_command",
                save_output=save_output
            ),
            'invalid_params': self.test_execute_command(
                "get_element",
                {"invalid_param": "value"},
                save_output=save_output
            ),
            'invalid_timeout': self.test_execute_command(
                "getTitle",
                timeout=0,
                save_output=save_output
            ),
            'invalid_storage': self.test_storage_data(
                "invalid_type",
                save_output=save_output
            )
        }
        return results

    def run_comprehensive_test(self, save_report: bool = True):
        """Run comprehensive API test suite"""
        start_time = datetime.now()
        print(f"\n{Fore.CYAN}Starting Comprehensive Test Suite{Style.RESET_ALL}")
        print(f"Time: {start_time.isoformat()}")
        print("=" * 50)

        # First, check server connection
        try:
            response = requests.get(f"{self.base_url}/api/commands/list/")
            if response.status_code == 404:
                print(f"{Fore.RED}Server is running but API endpoints are not found. Check URL configuration.{Style.RESET_ALL}")
            elif not response.ok:
                print(f"{Fore.RED}Server returned error: {response.status_code}{Style.RESET_ALL}")
        except requests.exceptions.ConnectionError:
            print(f"{Fore.RED}Could not connect to server at {self.base_url}{Style.RESET_ALL}")
            return None, None

        test_results = {
            'timestamp': start_time.isoformat(),
            'available_commands': self.test_list_commands(save_output=save_report),
            'basic_dom': self.test_basic_dom_commands(save_output=save_report),
            'storage': self.test_storage_commands(save_output=save_report),
            'error_cases': self.test_error_cases(save_output=save_report),
            'history': self.test_command_history(save_output=save_report)
        }

        # Generate summary
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        total_tests = len(self.test_results)
        successful_tests = len([t for t in self.test_results if t['success']])

        summary = {
            'total_tests': total_tests,
            'successful_tests': successful_tests,
            'failed_tests': total_tests - successful_tests,
            'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
            'duration_seconds': duration,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat()
        }

        # Print summary
        print(f"\n{Fore.CYAN}Test Summary:{Style.RESET_ALL}")
        print(f"Total Tests: {total_tests}")
        print(f"Successful: {Fore.GREEN}{successful_tests}{Style.RESET_ALL}")
        print(f"Failed: {Fore.RED}{summary['failed_tests']}{Style.RESET_ALL}")
        print(f"Success Rate: {Fore.GREEN}{summary['success_rate']:.2f}%{Style.RESET_ALL}")
        print(f"Duration: {duration:.2f} seconds")

        if save_report:
            self._save_summary_report(test_results, summary)

        return test_results, summary

    def _save_summary_report(self, test_results: Dict, summary: Dict):
        """Save test summary report"""
        reports_dir = Path('test_reports')
        reports_dir.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"comprehensive_test_report_{timestamp}.json"

        report = {
            'summary': summary,
            'results': test_results,
            'individual_tests': self.test_results,
            'environment': {
                'base_url': self.base_url,
                'api_base': self.api_base,
                'timestamp': datetime.now().isoformat()
            }
        }

        with open(reports_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)

        print(f"\nTest report saved to: {filename}")


def main():
    parser = argparse.ArgumentParser(description='Test Automation API')
    parser.add_argument('test', choices=[
        'list',  # List available commands
        'basic',  # Basic DOM commands
        'storage',  # Storage commands
        'errors',  # Error cases
        'history',  # Command history
        'element',  # Test specific element
        'comprehensive',  # Run all tests
    ], help='Test to run')

    # Optional arguments
    parser.add_argument('--type',
                        help='Command type filter for list command (storage, navigation, dom)')
    parser.add_argument('--selector',
                        default='body',
                        help='Element selector for element test')
    parser.add_argument('--url',
                        default='http://localhost:1234',
                        help='Base URL for API')
    parser.add_argument('--timeout',
                        type=int,
                        default=10,
                        help='Command timeout in seconds')
    parser.add_argument('--save',
                        action='store_true',
                        help='Save test output to file')
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='Enable verbose output')
    parser.add_argument('--format',
                        choices=['simple', 'full'],
                        default='full',
                        help='Response format for list command')
    parser.add_argument('--limit',
                        type=int,
                        default=100,
                        help='Maximum number of results to return for history')
    parser.add_argument('--status',
                        choices=['success', 'error'],
                        help='Filter history by status')

    args = parser.parse_args()

    # Set logging level based on verbose flag
    if args.verbose:
        logger.setLevel(logging.DEBUG)

    # Validate timeout
    if args.timeout < 1 or args.timeout > 60:
        print(f"{Fore.RED}Error: Timeout must be between 1 and 60 seconds{Style.RESET_ALL}")
        sys.exit(1)

    # Create reports directory if saving output
    if args.save:
        reports_dir = Path('test_reports')
        try:
            reports_dir.mkdir(exist_ok=True)
            print(f"{Fore.GREEN}Test reports will be saved to: {reports_dir.absolute()}{Style.RESET_ALL}")
        except Exception as e:
            print(f"{Fore.RED}Error creating reports directory: {str(e)}{Style.RESET_ALL}")
            sys.exit(1)

    # Create tester instance
    try:
        tester = AutomationAPITester(args.url)

        # Print test configuration
        if args.verbose:
            print(f"\n{Fore.CYAN}Test Configuration:{Style.RESET_ALL}")
            print(f"Base URL: {args.url}")
            print(f"Test Type: {args.test}")
            print(f"Timeout: {args.timeout} seconds")
            print(f"Save Output: {args.save}")
            print("=" * 50)

        # Run selected test
        if args.test == 'list':
            params = {
                'type': args.type,
                'format': args.format
            }
            tester.test_list_commands(command_type=args.type, save_output=args.save)

        elif args.test == 'basic':
            tester.test_basic_dom_commands(args.save)

        elif args.test == 'storage':
            tester.test_storage_commands(args.save)

        elif args.test == 'errors':
            tester.test_error_cases(args.save)

        elif args.test == 'history':
            tester.test_command_history(
                limit=args.limit,
                status=args.status,
                save_output=args.save
            )

        elif args.test == 'element':
            if not args.selector:
                print(f"{Fore.RED}Error: Selector is required for element test{Style.RESET_ALL}")
                sys.exit(1)

            tester.test_execute_command(
                "get_element",
                {"selector": args.selector},
                args.timeout,
                args.save
            )

        elif args.test == 'comprehensive':
            print(f"\n{Fore.CYAN}Running Comprehensive Test Suite{Style.RESET_ALL}")
            results, summary = tester.run_comprehensive_test(save_report=args.save)

            if not results:
                print(f"{Fore.RED}Comprehensive test failed to complete{Style.RESET_ALL}")
                sys.exit(1)

    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}Test execution interrupted by user{Style.RESET_ALL}")
        sys.exit(1)

    except requests.exceptions.ConnectionError:
        print(f"\n{Fore.RED}Error: Could not connect to server at {args.url}")
        print("Please make sure the server is running and the URL is correct{Style.RESET_ALL}")
        sys.exit(1)

    except Exception as e:
        print(f"\n{Fore.RED}Error running tests: {str(e)}{Style.RESET_ALL}")
        if logger.level == logging.DEBUG:
            import traceback
            print("\nStacktrace:")
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"{Fore.RED}Fatal error: {str(e)}{Style.RESET_ALL}")
        sys.exit(1)

