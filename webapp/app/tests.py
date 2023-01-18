import unittest
from selenium import webdriver
from project.settings import AZURE_CONFIG
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

tmp_folder = "/tmp"
url_init = AZURE_CONFIG.azure_host
idx = url_init.index('.')
url = url_init[:idx] + '-dev' + url_init[idx:]

class NotLoggedInTestCases(unittest.TestCase):
    def setUp(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('disable-infobars')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.browser = webdriver.Chrome(
            options=self.chrome_options, executable_path="/usr/bin/chromedriver")
        self.browser.delete_all_cookies()
        self.browser.maximize_window()
        try:
            element = self.browser.find_element(By.XPATH, '/html/body/footer')
            self.browser.execute_script("""
            var element = arguments[0];
            element.parentNode.removeChild(element);
            """, element)
        except Exception:
            pass


    def test_sees_not_signed_in_message(self):
        self.browser.get(f"https://{url}")
        self.assertTrue("You're not signed in." in self.browser.page_source)

    def test_can_view_category_page(self):
        self.browser.get(f"https://{url}")
        first_view = self.browser.find_element(
            By.ID, 'view_category0')
        first_view.click()
        visible_new_page = True
        try:
            WebDriverWait(self.browser, 20).until(
                EC.presence_of_element_located((By.ID, "category_name")))
        except Exception:
            visible_new_page = False
        self.assertTrue(visible_new_page)

    def test_can_see_cart(self):
        self.browser.get(f"https://{url}/cart")
        self.assertTrue("Shopping Cart" in self.browser.page_source)

    def test_can_add_product_to_cart_and_see_it(self):
        self.browser.get(f"https://{url}")
        category_first_view = self.browser.find_element(
            By.ID, 'view_category0')
        category_first_view.click()
        product_first_view = self.browser.find_element( By.ID, 'product_view0')
        product_name = self.browser.find_element(
            By.ID, 'product_name0').text
        product_first_view.click()
        self.assertEqual(product_name, self.browser.find_element(
            By.ID, 'product_name').text)
        product_add_to_cart = self.browser.find_element(
            By.ID, "add_to_cart")
        product_add_to_cart.click()
        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.ID, '0')))
        self.assertTrue(product_name in self.browser.page_source)

    def test_cannot_access_order_history(self):
        self.browser.get(f"https://{url}/order/history/")
        self.assertTrue("401: Unauthorized" in self.browser.page_source)

    def tearDown(self):
        self.browser.delete_all_cookies()
        self.browser.execute_script('window.localStorage.clear()')
        self.browser.execute_script('window.sessionStorage.clear()')
        self.browser.quit()


class LoggedInTestCases(unittest.TestCase):
    def setUp(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('disable-infobars')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.browser = webdriver.Chrome(
            options=self.chrome_options, executable_path="/usr/bin/chromedriver")
        self.browser.delete_all_cookies()
        self.browser.maximize_window()
        self.browser.get(f"https://{url}")
        sign_in = self.browser.find_element(
            By.XPATH, '//*[@id="navbarCollapse"]/div/ul/li[1]/a')
        sign_in.click()

        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.ID, "email")))

        username_input = self.browser.find_element(By.ID, 'email')
        username_input.clear()
        username_input.send_keys("test_user@test.pl")
        password_input = self.browser.find_element(By.ID, 'password')
        password_input.clear()
        password_input.send_keys("1P@ssw0rd!")
        self.browser.find_element(By.ID, 'next').click()

    def test_sees_signed_in_message(self):
        self.browser.get(f"https://{url}")
        self.assertTrue("You're signed in" in self.browser.page_source)

    def tearDown(self):
        self.browser.delete_all_cookies()
        self.browser.execute_script('window.localStorage.clear()')
        self.browser.execute_script('window.sessionStorage.clear()')
        self.browser.quit()


class LoggedInAdminTestCases(unittest.TestCase):
    def setUp(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument('--headless')
        self.chrome_options.add_argument('--no-sandbox')
        self.chrome_options.add_argument('--disable-gpu')
        self.chrome_options.add_argument('disable-infobars')
        self.chrome_options.add_argument('--disable-extensions')
        self.chrome_options.add_argument("--window-size=1920,1080")
        self.browser = webdriver.Chrome(
            options=self.chrome_options, executable_path="/usr/bin/chromedriver")
        self.browser.delete_all_cookies()
        self.browser.maximize_window()
        self.browser.get(f"https://{url}")
        sign_in = self.browser.find_element(
            By.XPATH, '//*[@id="navbarCollapse"]/div/ul/li[1]/a')
        sign_in.click()

        WebDriverWait(self.browser, 20).until(
            EC.presence_of_element_located((By.ID, "email")))

        username_input = self.browser.find_element(By.ID, 'email')
        username_input.clear()
        username_input.send_keys("test_admin@test.pl")
        password_input = self.browser.find_element(By.ID, 'password')
        password_input.clear()
        password_input.send_keys("!P@ssw0rd1")
        self.browser.find_element(By.ID, 'next').click()

    def test_sees_signed_in_message(self):
        self.browser.get(f"https://{url}")
        self.assertTrue("as an admin" in self.browser.page_source)

    def tearDown(self):
        self.browser.delete_all_cookies()
        self.browser.execute_script('window.localStorage.clear()')
        self.browser.execute_script('window.sessionStorage.clear()')
        self.browser.quit()
