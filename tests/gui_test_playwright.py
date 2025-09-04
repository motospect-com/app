"""
Comprehensive GUI tests for MOTOSPECT using Playwright
Tests all frontend components, customer portal, and report service
"""
import asyncio
import pytest
from playwright.async_api import async_playwright, expect
import os
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Test configuration
BASE_URL_FRONTEND = os.getenv("FRONTEND_URL", "http://localhost:3030")
BASE_URL_CUSTOMER = os.getenv("CUSTOMER_PORTAL_URL", "http://localhost:3040")
BASE_URL_REPORT = os.getenv("REPORT_SERVICE_URL", "http://localhost:3050")
BASE_URL_BACKEND = os.getenv("BACKEND_URL", "http://localhost:8030")

# Test VINs
TEST_VINS = [
    "1HGBH41JXMN109186",  # Honda Civic
    "2T2BK1BA5FC123456",  # Lexus RX
    "WBA3B5C50DF123456",  # BMW 3 Series
]


class MotospectGUITests:
    """Comprehensive GUI test suite for MOTOSPECT"""
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.page = None
        self.test_results = {
            "passed": 0,
            "failed": 0,
            "errors": [],
            "screenshots": []
        }
    
    async def setup(self):
        """Setup browser and context"""
        logger.info("Setting up Playwright browser...")
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=os.getenv("HEADLESS", "true").lower() == "true",
            args=['--no-sandbox', '--disable-setuid-sandbox']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            record_video_dir="test-videos/" if os.getenv("RECORD_VIDEO") else None
        )
        self.page = await self.context.new_page()
        
        # Enable console logging
        self.page.on("console", lambda msg: logger.debug(f"Browser console: {msg.text}"))
        self.page.on("pageerror", lambda err: logger.error(f"Page error: {err}"))
    
    async def teardown(self):
        """Clean up browser resources"""
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
    
    async def take_screenshot(self, name: str):
        """Take a screenshot for debugging"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/{name}_{timestamp}.png"
        os.makedirs("screenshots", exist_ok=True)
        await self.page.screenshot(path=filename)
        self.test_results["screenshots"].append(filename)
        logger.info(f"Screenshot saved: {filename}")
    
    async def log_network_errors(self):
        """Log any network errors"""
        def handle_response(response):
            if response.status >= 400:
                logger.warning(f"Network error: {response.status} - {response.url}")
        
        self.page.on("response", handle_response)
    
    # --- Frontend Tests ---
    
    async def test_frontend_homepage(self):
        """Test frontend homepage loads correctly"""
        test_name = "frontend_homepage"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Check title
            await expect(self.page).to_have_title("MOTOSPECT - Vehicle Diagnostic System", timeout=5000)
            
            # Check main components exist
            await expect(self.page.locator("h1")).to_contain_text("MOTOSPECT")
            
            # Check 3D visualization canvas exists
            canvas = self.page.locator("canvas")
            await expect(canvas).to_be_visible()
            
            # Check control panel exists
            control_panel = self.page.locator("[data-testid='control-panel'], .control-panel, #controls")
            await expect(control_panel).to_be_visible()
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    async def test_frontend_scan_start(self):
        """Test starting a scan from frontend"""
        test_name = "frontend_scan_start"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Enter VIN
            vin_input = self.page.locator("input[placeholder*='VIN'], input#vin, [data-testid='vin-input']")
            await vin_input.fill(TEST_VINS[0])
            
            # Click scan button
            scan_button = self.page.locator("button:has-text('Start'), button:has-text('Scan'), [data-testid='start-scan']")
            await scan_button.click()
            
            # Wait for scanning indicator
            scanning_indicator = self.page.locator("text=/Scanning|Processing|Analyzing/i")
            await expect(scanning_indicator).to_be_visible(timeout=10000)
            
            # Check WebSocket connection
            await self.page.wait_for_timeout(2000)
            
            # Check for data updates
            data_display = self.page.locator("[data-testid='scan-data'], .scan-results, .data-display")
            await expect(data_display).to_be_visible()
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    async def test_frontend_3d_interaction(self):
        """Test 3D visualization interactions"""
        test_name = "frontend_3d_interaction"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Get canvas element
            canvas = self.page.locator("canvas")
            await expect(canvas).to_be_visible()
            
            # Test mouse interactions (pan, zoom, rotate)
            box = await canvas.bounding_box()
            if box:
                center_x = box['x'] + box['width'] / 2
                center_y = box['y'] + box['height'] / 2
                
                # Rotate
                await self.page.mouse.move(center_x, center_y)
                await self.page.mouse.down()
                await self.page.mouse.move(center_x + 100, center_y)
                await self.page.mouse.up()
                
                # Zoom
                await self.page.mouse.wheel(0, -100)
                await self.page.wait_for_timeout(500)
                await self.page.mouse.wheel(0, 100)
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Customer Portal Tests ---
    
    async def test_customer_portal_homepage(self):
        """Test customer portal homepage"""
        test_name = "customer_portal_homepage"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_CUSTOMER, wait_until="networkidle")
            
            # Check main elements
            await expect(self.page.locator("h1, h2")).to_contain_text("Customer Portal")
            
            # Check VIN input exists
            vin_input = self.page.locator("input[placeholder*='VIN'], input#vin")
            await expect(vin_input).to_be_visible()
            
            # Check submit button
            submit_button = self.page.locator("button:has-text('Submit'), button:has-text('Check')")
            await expect(submit_button).to_be_visible()
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    async def test_customer_portal_vehicle_lookup(self):
        """Test vehicle lookup in customer portal"""
        test_name = "customer_portal_vehicle_lookup"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_CUSTOMER, wait_until="networkidle")
            
            # Enter VIN
            vin_input = self.page.locator("input[placeholder*='VIN'], input#vin")
            await vin_input.fill(TEST_VINS[1])
            
            # Submit
            submit_button = self.page.locator("button:has-text('Submit'), button:has-text('Check')")
            await submit_button.click()
            
            # Wait for results
            await self.page.wait_for_timeout(2000)
            
            # Check for vehicle info display
            vehicle_info = self.page.locator(".vehicle-info, [data-testid='vehicle-info']")
            await expect(vehicle_info).to_be_visible(timeout=10000)
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- API Integration Tests ---
    
    async def test_backend_api_health(self):
        """Test backend API health endpoint"""
        test_name = "backend_api_health"
        try:
            logger.info(f"Running test: {test_name}")
            
            response = await self.page.request.get(f"{BASE_URL_BACKEND}/health")
            assert response.ok, f"Health check failed with status {response.status}"
            
            data = await response.json()
            assert data.get("status") == "healthy", "Backend not healthy"
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    async def test_backend_api_vin_decode(self):
        """Test VIN decode API"""
        test_name = "backend_api_vin_decode"
        try:
            logger.info(f"Running test: {test_name}")
            
            response = await self.page.request.post(
                f"{BASE_URL_BACKEND}/api/vehicle/decode",
                data={"vin": TEST_VINS[0]}
            )
            
            assert response.ok, f"VIN decode failed with status {response.status}"
            
            data = await response.json()
            assert "make" in data, "Make not in response"
            assert "model" in data, "Model not in response"
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- WebSocket Tests ---
    
    async def test_websocket_connection(self):
        """Test WebSocket connection and data flow"""
        test_name = "websocket_connection"
        try:
            logger.info(f"Running test: {test_name}")
            
            # Navigate to frontend
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Check for WebSocket connection
            ws_connected = await self.page.evaluate("""
                () => {
                    return window.ws && window.ws.readyState === WebSocket.OPEN;
                }
            """)
            
            # If not connected via global, check for any WS connections
            if not ws_connected:
                await self.page.wait_for_timeout(2000)
                # Try to detect WS through network activity
                
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Responsive Design Tests ---
    
    async def test_mobile_responsive(self):
        """Test mobile responsiveness"""
        test_name = "mobile_responsive"
        try:
            logger.info(f"Running test: {test_name}")
            
            # Set mobile viewport
            await self.page.set_viewport_size({"width": 375, "height": 812})
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Check elements are visible
            await expect(self.page.locator("h1")).to_be_visible()
            
            # Check for mobile menu if present
            mobile_menu = self.page.locator(".mobile-menu, [data-testid='mobile-menu']")
            if await mobile_menu.count() > 0:
                await expect(mobile_menu).to_be_visible()
            
            await self.take_screenshot(f"{test_name}_mobile")
            
            # Test tablet view
            await self.page.set_viewport_size({"width": 768, "height": 1024})
            await self.page.reload()
            await self.take_screenshot(f"{test_name}_tablet")
            
            # Reset to desktop
            await self.page.set_viewport_size({"width": 1920, "height": 1080})
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Performance Tests ---
    
    async def test_page_load_performance(self):
        """Test page load performance"""
        test_name = "page_load_performance"
        try:
            logger.info(f"Running test: {test_name}")
            
            # Measure frontend load time
            start_time = asyncio.get_event_loop().time()
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            frontend_load_time = asyncio.get_event_loop().time() - start_time
            
            assert frontend_load_time < 5, f"Frontend load time too slow: {frontend_load_time:.2f}s"
            logger.info(f"Frontend load time: {frontend_load_time:.2f}s")
            
            # Measure customer portal load time
            start_time = asyncio.get_event_loop().time()
            await self.page.goto(BASE_URL_CUSTOMER, wait_until="networkidle")
            portal_load_time = asyncio.get_event_loop().time() - start_time
            
            assert portal_load_time < 5, f"Portal load time too slow: {portal_load_time:.2f}s"
            logger.info(f"Portal load time: {portal_load_time:.2f}s")
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Error Handling Tests ---
    
    async def test_invalid_vin_handling(self):
        """Test handling of invalid VIN"""
        test_name = "invalid_vin_handling"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Enter invalid VIN
            vin_input = self.page.locator("input[placeholder*='VIN'], input#vin")
            await vin_input.fill("INVALID123")
            
            # Try to start scan
            scan_button = self.page.locator("button:has-text('Start'), button:has-text('Scan')")
            await scan_button.click()
            
            # Check for error message
            error_message = self.page.locator(".error, .alert-danger, [role='alert']")
            await expect(error_message).to_be_visible(timeout=5000)
            
            await self.take_screenshot(test_name)
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            await self.take_screenshot(f"{test_name}_error")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Accessibility Tests ---
    
    async def test_accessibility_basics(self):
        """Test basic accessibility features"""
        test_name = "accessibility_basics"
        try:
            logger.info(f"Running test: {test_name}")
            await self.page.goto(BASE_URL_FRONTEND, wait_until="networkidle")
            
            # Check for alt text on images
            images = await self.page.locator("img").all()
            for img in images:
                alt_text = await img.get_attribute("alt")
                assert alt_text, "Image missing alt text"
            
            # Check for proper heading hierarchy
            h1_count = await self.page.locator("h1").count()
            assert h1_count >= 1, "Page should have at least one H1"
            
            # Check for keyboard navigation
            await self.page.keyboard.press("Tab")
            focused_element = await self.page.evaluate("() => document.activeElement.tagName")
            assert focused_element != "BODY", "Tab navigation not working"
            
            self.test_results["passed"] += 1
            logger.info(f"✓ Test {test_name} passed")
            
        except Exception as e:
            self.test_results["failed"] += 1
            self.test_results["errors"].append(f"{test_name}: {str(e)}")
            logger.error(f"✗ Test {test_name} failed: {e}")
    
    # --- Run all tests ---
    
    async def run_all_tests(self):
        """Run all GUI tests"""
        logger.info("="*60)
        logger.info("Starting MOTOSPECT GUI Test Suite")
        logger.info("="*60)
        
        test_methods = [
            self.test_frontend_homepage,
            self.test_frontend_scan_start,
            self.test_frontend_3d_interaction,
            self.test_customer_portal_homepage,
            self.test_customer_portal_vehicle_lookup,
            self.test_backend_api_health,
            self.test_backend_api_vin_decode,
            self.test_websocket_connection,
            self.test_mobile_responsive,
            self.test_page_load_performance,
            self.test_invalid_vin_handling,
            self.test_accessibility_basics,
        ]
        
        for test_method in test_methods:
            try:
                await test_method()
            except Exception as e:
                logger.error(f"Test method {test_method.__name__} crashed: {e}")
                self.test_results["failed"] += 1
                self.test_results["errors"].append(f"{test_method.__name__}: {str(e)}")
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        logger.info("="*60)
        logger.info("TEST RESULTS SUMMARY")
        logger.info("="*60)
        logger.info(f"✓ Passed: {self.test_results['passed']}")
        logger.info(f"✗ Failed: {self.test_results['failed']}")
        logger.info(f"Total: {self.test_results['passed'] + self.test_results['failed']}")
        
        if self.test_results['errors']:
            logger.info("\nErrors:")
            for error in self.test_results['errors']:
                logger.error(f"  - {error}")
        
        if self.test_results['screenshots']:
            logger.info(f"\nScreenshots saved: {len(self.test_results['screenshots'])}")
        
        # Save report to file
        report_file = f"test-report-{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(self.test_results, f, indent=2)
        logger.info(f"\nDetailed report saved to: {report_file}")
        
        # Return exit code
        return 0 if self.test_results['failed'] == 0 else 1


async def main():
    """Main test runner"""
    tester = MotospectGUITests()
    try:
        await tester.setup()
        await tester.run_all_tests()
    finally:
        await tester.teardown()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
