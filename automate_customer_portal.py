import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

def automate_customer_portal():
    # Set up Chrome options
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # Initialize the Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    try:
        # Navigate to the customer portal
        print("Navigating to customer portal...")
        driver.get("http://localhost:3040/")
        
        # Wait for the VIN input to be visible and enter the VIN
        print("Entering VIN...")
        vin_input = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
        )
        vin_input.send_keys("TEST_VIN")
        
        # Find and click the submit button
        print("Submitting form...")
        submit_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "button[type='submit']"))
        )
        submit_button.click()
        
        # Wait for the scanning to complete (you might need to adjust the timeout)
        print("Waiting for scanning to complete...")
        WebDriverWait(driver, 30).until(
            EC.visibility_of_element_located((By.CLASS_NAME, "scan-complete"))
        )
        
        print("Automation completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the browser
        driver.quit()

if __name__ == "__main__":
    automate_customer_portal()
