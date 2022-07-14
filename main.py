from bot import Bot


if __name__ == '__main__':
    mail = 'stockastate@gmail.com'  # input('Введите логин аккаунта: ')
    password = '567sT678!'  # input('Введите пароль аккаунта: ')
    certificate_name = ''  # input('Введите название сертификата: ')
    tin = ''  # input('Введите ИНН для поиска: ')
    keyword = ''  # input('Введите ключевую фразу или нажмите Enter для выбора всех процедур: ')
    first_desc = ''# input('Введите название ТРУ: ')
    second_desc = ''  # input('Введите описание ТРУ: ')
    purchase_number = input('Введите номер заказа: ')
    bets_to_exclude = input('Введите номера ставок для исключения через пробел: ').split()  # Здесь номера закупок через пробел которые нужно исключить

    bot = Bot(mail=mail,
              password=password,
              certificate_name=certificate_name,
              tin=tin,
              keyword=keyword,
              first_desc=first_desc,
              second_desc=second_desc,
              bets_to_exclude=bets_to_exclude,
              purchase_number=purchase_number)

    bot.login()
    bot.make_bet()

    input()

