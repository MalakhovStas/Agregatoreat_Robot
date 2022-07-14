from time import sleep

from pywinauto.application import Application
from selenium.common.exceptions import StaleElementReferenceException, ElementClickInterceptedException, \
    TimeoutException
from selenium.webdriver import Chrome, ActionChains, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

from config import MAIN_URL, TRADES_URL, LOGIN_URL

from database import Controller


class Bot:
    def __init__(self, mail: str, password: str, certificate_name: str, tin: str, keyword: str, first_desc: str,
                 second_desc: str, bets_to_exclude: list, purchase_number: str, wait_time: int = 30,
                 error_time: int = 1, cards_time: int = 3):
        self.service = Service(executable_path=ChromeDriverManager().install())
        self.options = Options()
        self.options.add_argument('--start-maximized')
        self.options.add_extension('plugin.crx')
        self.driver: Chrome = Chrome(service=self.service, options=self.options)
        self.waiter: WebDriverWait = WebDriverWait(self.driver, wait_time)
        self.error_waiter: WebDriverWait = WebDriverWait(self.driver, error_time)
        self.cards_waiter: WebDriverWait = WebDriverWait(self.driver, cards_time)
        self.actions: ActionChains = ActionChains(self.driver)
        self.mail = mail.strip()
        self.password = password.strip()
        self.certificate_name = certificate_name.strip()
        self.tin = tin.strip()
        self.keyword = keyword.strip()
        self.first_desc = first_desc.strip()
        self.second_desc = second_desc.strip()
        self.bets_to_exclude: list = [int(bet_to_exclude) for bet_to_exclude in bets_to_exclude if len(bet_to_exclude)]
        self. purchase_number = purchase_number.strip()

    def login(self):
        self.driver.get(LOGIN_URL)
        login_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Username"]')))
        login_input.send_keys(self.mail)
        password_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[name="Password"]')))
        password_input.send_keys(self.password)
        #TODO удалить старый клик на кнопку входа в лк
        # login_button = self.waiter.until(
        #     EC.visibility_of_element_located((By.CSS_SELECTOR, 'button[value="login"]')))
        login_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '#loginForm > fieldset > button')))
        login_button.click()
        self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))

    def check_login(self):
        """Функция проверки доступа к личному кабинету"""
        try:
            log = self.waiter.until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'span.login-btn__caption')))  # Ждём загрузки ярлыка
            if log.text.strip().lower() == 'личный кабинет':  # Если текст на ярлыке - 'личный кабинет'
                login_refresh_button = self.waiter.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, 'button.btn.btn--yellow.login-btn')))
                login_refresh_button.click()  # Нажимаем кнопку на ярлыке
                enter_as_refresh = self.waiter.until(
                    EC.visibility_of_all_elements_located(
                        (By.CSS_SELECTOR, 'a.lk-menu-item.ng-star-inserted:nth-of-type(1)')))
                enter_as_refresh[0].click()  # В выпадающем списке кликаем поле 'поставщик'
        except Exception:
            self.check_login()  # В случае ошибки вызывает себя рекурсивно

    def set_only_eat_filter(self):
        """Включает флаг - 'Показывать только закупки на ЕАТ'"""
        only_eat_switch = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'span.ui-inputswitch-slider')))
        self.actions.move_to_element(only_eat_switch).click(on_element=only_eat_switch).perform()

    def set_number_filter(self):
        """Записывает номер закупки в поле фильтра"""
        if self.purchase_number:
            print('печать')
            keyword_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-3-input')))
            self.actions.move_to_element(keyword_input).perform()
            keyword_input.send_keys(self.purchase_number)

    def set_keyword_filter(self):
        """Записывает 'Наименование ТРУ' в поле фильтра"""
        keyword_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-2-input')))
        self.actions.move_to_element(keyword_input).perform()
        keyword_input.send_keys(self.keyword)

    def set_tin_filter(self):
        """Записывает ИНН в поле фильтра"""
        tin_input = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'input#filterField-13-autocomplete')))
        self.actions.move_to_element(tin_input).perform()
        tin_input.send_keys(self.tin)

    def apply_filters(self):
        """Нажимает кнопку 'показать' - применяем введенные значения фильтров"""
        apply_filters_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#applyFilterButton')))
        self.actions.move_to_element(apply_filters_button).click(on_element=apply_filters_button).perform()

    def get_cards(self):
        """Находит все карточки лотов на странице"""
        all_cards = self.cards_waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))
        for card in all_cards:
            """Находит номер заказа каждой карточки и вызываем функцию  функцию Controller.add_bet(int(номер заказа)) 
            запсывает его в базу данных"""
            bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber')
            Controller.add_bet(bet_id=int(bet_id.text))

    def goto_place_button(self):
        """Скролит страничку"""
        y_offset = 10
        while True:
            try:
                place_bet_button = self.waiter.until(EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.c-btn-group > button.c-btn.c-btn--primary')))  # это не нашел
                place_bet_button.click()
            except ElementClickInterceptedException:
                self.driver.execute_script(f'window.scroll(0, {y_offset})')  # это скрол
                y_offset += 10
            else:
                break

    def write_descriptions(self):
        select_tru_buttons = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))  # это не нашел
        for select_tru_button in select_tru_buttons:
            y_offset = -10
            while True:
                try:
                    select_tru_button.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')  # это скрол
                    y_offset -= 10
                else:
                    break
            create_new_button = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, '.tru-description-modal__action:nth-of-type(3)')))
            create_new_button.click()
            tru_name_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'input[formcontrolname="offerName"]')))
            tru_name_input.send_keys(self.first_desc)
            tru_desc_input = self.waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'textarea[formcontrolname="offerDescription"]')))
            tru_desc_input.send_keys(self.second_desc)
            accept_tru_button = self.waiter.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, '.modal-window__buttons-container > button:nth-of-type(2)')))
            accept_tru_button.click()

    def place_bet(self):
        send_bet_button = self.waiter.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR, '.c-btn-group > button.c-btn.c-btn--primary')))
        self.actions.move_to_element(send_bet_button).perform()
        self.goto_place_button()
        try:
            self.error_waiter.until(
                EC.visibility_of_element_located((By.CSS_SELECTOR, 'svg-icon.select-tru__icon.ng-star-inserted')))
        except TimeoutException:
            pass
        else:
            self.write_descriptions()
        is_price_with_tax_checkboxes = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'p-checkbox[formcontrolname="isPriceWithTax"]')))
        for checkbox in is_price_with_tax_checkboxes:
            y_offset = -10
            while True:
                try:
                    self.waiter.until(EC.element_to_be_clickable(checkbox))
                    checkbox.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    y_offset -= 10
                else:
                    break
        price_inputs = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'td.col-price.col-editable > input')))
        for price_input in price_inputs:
            y_offset = 10
            up = True
            while True:
                try:
                    price_input.send_keys(Keys.BACKSPACE*20)
                    price_input.send_keys(Keys.DELETE*20)
                    price_input.send_keys('0,01')
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    if y_offset < 500 and up:
                        y_offset += 10
                    else:
                        up = False
                        y_offset -= 10
                else:
                    break
        tax_percent_dropdowns = self.waiter.until(
            EC.visibility_of_all_elements_located((By.CSS_SELECTOR, 'p-dropdown[formcontrolname="taxPercent"]')))
        for dropdown in tax_percent_dropdowns:
            y_offset = -10
            while True:
                try:
                    dropdown.click()
                except ElementClickInterceptedException:
                    self.driver.execute_script(f'window.scroll(0, {y_offset});')
                    y_offset -= 10
                else:
                    break
            no_tax_item = dropdown.find_element(
                By.CSS_SELECTOR, '.ui-dropdown-items-wrapper p-dropdownitem:nth-of-type(1)')
            no_tax_item.click()
        self.goto_place_button()
        confirm_bet_button = self.waiter.until(
            EC.visibility_of_element_located(
                (By.CSS_SELECTOR,
                 '.dynamic-modal-window__buttons-container > button.c-btn.c-btn--secondary:nth-of-type(2)')))
        confirm_bet_button.click()
        sign_in_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, 'button#signButton')))
        sign_in_button.click()
        try:
            app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
            confirmWin = app.window(title_re=u'Подтверждение доступа')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'&Да']
                yesBtn.click()
        except Exception as e:
            sleep(2)
            try:
                app = Application(backend="uia").connect(title="Подтверждение доступа", timeout=5)
                confirmWin = app.window(title_re=u'Подтверждение доступа')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'&Да']
                    yesBtn.click()
            except Exception as e:
                return False
        certificates = self.waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'span.fullname')))
        for certificate in certificates:
            if self.certificate_name.strip().lower() == certificate.text.strip().lower():
                certificate.click()
                break
        sign_in_button = self.waiter.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, '.modal-wrapper__btns > button.c-btn.c-btn--primary')))
        sign_in_button.click()
        try:
            app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
            confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
            if confirmWin.exists(timeout=10, retry_interval=1):
                confirmWin.set_focus()
                yesBtn = confirmWin[u'ОК']
                yesBtn.click()
        except Exception as e:
            sleep(2)
            try:
                app = Application(backend="uia").connect(title_re="Выбор ключевого носителя - КриптоПро CSP", timeout=5)
                confirmWin = app.window(title_re=u'Выбор ключевого носителя - КриптоПро CSP')
                if confirmWin.exists(timeout=10, retry_interval=1):
                    confirmWin.set_focus()
                    yesBtn = confirmWin[u'ОК']
                    yesBtn.click()
            except Exception as e:
                return False
        return True

    def work(self):
        #TODO потом включить
        self.check_login()
        try:
            self.get_cards()
        except TimeoutException:
            return False

        """Находит все карточки лотов на странице"""
        all_cards = self.waiter.until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'app-purchase-card.ng-star-inserted')))
        for card in all_cards:
            bet_id = card.find_element(By.CSS_SELECTOR, 'h3#tradeNumber') # Находит номер закупки в карточке лота
            if not Controller.get_bet_status(int(bet_id.text)) and int(bet_id) not in self.bets_to_exclude:  # Если номера закупки нет среди исключений
                send_bet_button = card.find_element(By.CSS_SELECTOR, 'button#applicationSendButton')  # Находит
                send_bet_button.click()  # И кликает кнопку 'подать предложение'
                if self.place_bet():
                    Controller.update_bet_status(True, bet_id=int(bet_id.text))
                    return True
                else:
                    return False

    def make_bet(self):
        while True:
            self.driver.get(TRADES_URL)
            try:
                self.set_only_eat_filter()
                if self.keyword: self.set_keyword_filter()  # Запись ТРУ в поле фильтра
                if self.tin: self.set_tin_filter()  # Запись ИНН в поле фильтра
                if self.purchase_number: self.set_number_filter()  # Запись номера закупки в поле фильтра
                self.apply_filters()  # Применить фильтр
            except TimeoutException:
                print('Тут timeout и перезагрузка')
                self.driver.get(TRADES_URL)
                continue
            except Exception as e:
                print(f'Логи: {e}')
                continue
            try:
                self.work()
            except TimeoutException:
                print('Или тут timeout и перезагрузка')
                continue
            except Exception as e:
                print(f'Логи: {e}')
                continue
