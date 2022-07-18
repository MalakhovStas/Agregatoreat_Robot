from bot import Bot
from config import dev_git, dev_tm
from database import DataController
from colorama import init, Fore
# from art import tprint


def data_answer():
    init()
    answer = 'start'
    while answer not in ['y', 'n']:
        if answer == 'restart':
            print(f'{Fore.RED}Ошибка ввода! Нужно ввести "y" или "n"{Fore.RESET}')
        answer = input(f'Использовать сохранённые данные - y/n: ').lower() if \
            DataController.get_data() else 'n'

        answer = 'y' if answer == 'н' else answer
        answer = 'n' if answer == 'т' else answer

        if answer == 'y':
            mail, password, first_desc, second_desc, certificate_name, only_EAT, tin, \
            bets_to_exclude = DataController.get_data()

            print(f'\n{Fore.YELLOW}Логин: {Fore.RESET}{mail}\n{Fore.YELLOW}Пароль: {Fore.RESET}{password}\n'
                  f'{Fore.YELLOW}Hазвание ТРУ: {Fore.RESET}{first_desc}\n{Fore.YELLOW}Описание ТРУ: {Fore.RESET}'
                  f'{second_desc}\n{Fore.YELLOW}Название сертификата: {Fore.RESET}{certificate_name}\n'
                  f'{Fore.YELLOW}Флаг EAT: {Fore.RESET}{"вкл" if only_EAT == "1" else "выкл"}\n{Fore.YELLOW}ИНН для пои'
                  f'ска: {Fore.RESET}{tin}\n{Fore.YELLOW}Hомера лотов для исключения:{Fore.RESET}{bets_to_exclude}\n')

            return mail, password, first_desc, second_desc, certificate_name, only_EAT, tin, bets_to_exclude

        elif answer == 'n':
            mail = input('\nВведите логин аккаунта: ')
            password = input(f'Введите пароль аккаунта: ')

            first_desc = input('Введите название ТРУ для заполнения карточки: ')
            first_desc = 'ТРУ' if not len(first_desc.strip()) else first_desc

            second_desc = input('Введите описание ТРУ для заполнения карточки: ')
            second_desc = 'ТРУ' if not len(second_desc.strip()) else second_desc

            certificate_name = input('Введите название сертификата: ')

            only_EAT = input('Включить флаг EAT - 1/0: ')
            only_EAT = '0' if only_EAT != '1' else only_EAT

            tin = input('Введите ИНН для поиска или нажмите Enter: ')
            bets_to_exclude = input('Введите номера лотов для исключения через пробел: ')

            DataController.update_data(
                mail, password, first_desc, second_desc, certificate_name, only_EAT, tin, bets_to_exclude) if \
                DataController.get_data() else DataController.add_data(mail, password, first_desc, second_desc,
                                                                       certificate_name, only_EAT, tin, bets_to_exclude)

            return mail, password, first_desc, second_desc, certificate_name, only_EAT, tin, bets_to_exclude
        answer = 'restart'


if __name__ == '__main__':
    init()
    print(f'{Fore.GREEN}Last release dev: {Fore.BLUE}{dev_git}  {Fore.GREEN}|  {Fore.BLUE}{dev_tm}{Fore.RESET}\n')
    # tprint('AgregatorEAT-Bot')

    mail, password, first_desc, second_desc, certificate_name, only_EAT, tin, bets_to_exclude = data_answer()
    purchase_number = input('Введите номер лота для поиска или нажмите Enter: ')
    keyword = input('Введите ключевую фразу для поиска в наименовании или нажмите Enter: ')
    automatic_sbsc = 'n' #input('Подписывать лоты автоматически - y/n: ')

    bot = Bot(mail=mail,
              password=password,
              certificate_name=certificate_name,
              tin=tin,
              keyword=keyword,
              first_desc=first_desc,
              second_desc=second_desc,
              bets_to_exclude=bets_to_exclude,
              purchase_number=purchase_number,
              only_EAT=only_EAT,
              automatic_sbsc=automatic_sbsc)

    bot.login()
    bot.make_bet()

    input()


# Если не работает на windows ошибки в коде библиотек
# pip install setuptools==57.0.0 --force-reinstall
# pip install wheel==0.36.2 --force-reinstall
# pip uninstall comtypes
# pip install --no-cache-dir comtypes

# Чей-то логин пароль, с ними тестировал
# stockastate@gmail.com
# 567sT678!

# Настройки логера логуру хотел подключить.
# LOG_FMT = '{time:DD-MM-YYYY at HH:mm:ss} | {level: <8} | func: {function: ^15} | line: {line: >3} | message: {message}'
# logger.add(sink='logs/debug.log', format=LOG_FMT, level='INFO', diagnose=True, backtrace=False,
#            rotation="100 MB", retention=2, compression="zip")
