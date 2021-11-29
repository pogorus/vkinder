from random import randrange
from datetime import datetime
import time
import requests
import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
import vk_db


user_token = 'USER TOKEN'
token = 'TOKEN'

vk = vk_api.VkApi(token=token)
longpoll = VkLongPoll(vk)

vk_db.start_db()

class VkUser:
    def __init__(self, user_id, bdate, sex, city, counter = 0):
        self.user_id = user_id
        if len(bdate[0]) == 1:
            bdate[0] = f'0{bdate[0]}'
        if len(bdate[1]) == 1:
            bdate[1] = f'0{bdate[1]}'
        self.age = (int(datetime.today().strftime('%Y%m%d')) - int(''.join(bdate[::-1]))) // 10000
        self.sex = sex
        self.city = city
        self.counter = counter


def get_photo(id):
    response = requests.get('https://api.vk.com/method/photos.get',
                            params={'access_token': user_token, 'v': '5.131', 'album_id': 'profile',
                                    'extended': '1', 'owner_id': id}).json()

    photo_dict = {}
    for photo in response['response']['items']:
        photo_dict[photo['id']] = photo['likes']['count'] + photo['reposts']['count'] + photo['comments']['count']

    sorted_photo = sorted(photo_dict.items(), key=lambda item: item[1])
    return sorted_photo[-1:-4:-1]


def write_msg(user_id, message):
    vk.method('messages.send', {'user_id': user_id, 'message': message,  'random_id': randrange(10 ** 7)})


def send_attachment(user_id, owner_id, photo_id):
    vk.method('messages.send', {'user_id': user_id, 'message': '', 'attachment': f'photo{owner_id}_{photo_id}', 'random_id': randrange(10 ** 7)})


for event in longpoll.listen():
    if event.type == VkEventType.MESSAGE_NEW:

        if event.to_me:
            request = event.text
            user_id = event.user_id

            finder_params = {'access_token': token, 'v': '5.131', 'user_ids': request, 'fields': 'city, sex, bdate'}

            response = requests.get('https://api.vk.com/method/users.get', params=finder_params).json()

            try:
                if response['error']:
                    write_msg(user_id, 'Введите ID пользователя для которого хотите найти пару.')
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                user_id = event.user_id
                                finder_params = {'access_token': token, 'v': '5.131', 'user_ids': request, 'fields': 'city, sex, bdate'}
                                response = requests.get('https://api.vk.com/method/users.get', params=finder_params).json()
                                try:
                                    if response['response']:
                                        break
                                except KeyError:
                                    write_msg(user_id, 'Пользователя с данным ID не существует, проверьте правильность ввода, или введите другой ID.')
            except KeyError:
                pass

            finder_id = response['response'][0]['id']

            finders_list = vk_db.get_finders_list()

            if str(finder_id) in finders_list:
                bdate = vk_db.get_bdate(finder_id)
                sex = vk_db.get_sex(finder_id)
                city = vk_db.get_city(finder_id)
                counter = vk_db.get_counter(finder_id)

            else:
                try:
                    bdate = response['response'][0]['bdate'].split('.')
                except KeyError:
                    bdate = []
                try:
                    sex = response['response'][0]['sex']
                except KeyError:
                    sex = ''
                try:
                    city = response['response'][0]['city']['id']
                except KeyError:
                    city = ''
                counter = 0

                if bdate == [] or len(bdate) < 3:
                    write_msg(user_id, 'Укажите дату рождения в формате: дд.мм.гггг')
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                user_id = event.user_id
                                bdate = request.split('.')
                                if bdate == [] or len(bdate) < 3 or not 0 < int(bdate[0]) <= 31 or not 0 < int(bdate[1]) <= 12 or not 1900 < int(bdate[2]) < datetime.today().year:
                                    write_msg(user_id, 'Дата рождения указанна некорректно')
                                    write_msg(user_id, 'Укажите дату рождения в формате: дд.мм.гггг')
                                else:
                                    break

                if sex == '':
                    write_msg(user_id, 'Укажите пол: 1 - женский; 2 - мужской')
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                user_id = event.user_id
                                sex = request
                                if not 1 <= sex <= 2:
                                    write_msg(user_id, 'Пол указан некорректно')
                                    write_msg(user_id, 'Укажите пол: 1 - женский; 2 - мужской')
                                else:
                                    break

                if city == '':
                    write_msg(user_id, 'Укажите город')
                    for event in longpoll.listen():
                        if event.type == VkEventType.MESSAGE_NEW:
                            if event.to_me:
                                request = event.text
                                user_id = event.user_id
                                city = request.lower()
                                city_response = requests.get('https://api.vk.com/method/database.getCities',
                                        params={'access_token': user_token, 'v': '5.131', 'country_id': 1,
                                                'q': city, 'need_all': '0', 'count': 1}).json()
                                try:
                                    city = city_response['response']['items'][0]['id']
                                    break
                                except IndexError:
                                    write_msg(user_id, 'Город не найден')
                                    write_msg(user_id, 'Укажите город')

                if len(bdate[0]) == 1:
                    bdate[0] = f'0{bdate[0]}'
                if len(bdate[1]) == 1:
                    bdate[1] = f'0{bdate[1]}'

                vk_db.add_new_finder(finder_id, bdate, sex, city)

            user = VkUser(finder_id, bdate, sex, city, counter)

            search_params = {'access_token': user_token, 'v': '5.131', 'sort': 0,
                                                   'sex': 1 if user.sex == 2 else 2,
                                                   'count': 1, 'status': 6, 'age_from': user.age,
                                                   'age_to': user.age, 'offset': user.counter,
                                                   'has_photo': 1, 'city': user.city, 'fields': 'id',
                                                   'is_closed': 0}
            search_response = requests.get('https://api.vk.com/method/users.search', params=search_params).json()

            user.counter += 1
            vk_db.update_counter(finder_id)

            if search_response['response']['items'] == [] or search_response['response']['items'][0]['is_closed']:
                while search_response['response']['items'] == [] or search_response['response']['items'][0]['is_closed']:
                    search_params = {'access_token': user_token, 'v': '5.131', 'sort': 0,
                                     'sex': 1 if user.sex == 2 else 2,
                                     'count': 1, 'status': 6, 'age_from': user.age,
                                     'age_to': user.age, 'offset': user.counter,
                                     'has_photo': 1, 'city': user.city, 'fields': 'id',
                                     'is_closed': 0}
                    search_response = requests.get('https://api.vk.com/method/users.search', params=search_params).json()
                    user.counter += 1
                    vk_db.update_counter(finder_id)
                    time.sleep(0.5)

            found_id = search_response["response"]["items"][0]["id"]
            write_msg(user_id, f'https://vk.com/id{found_id}')

            photos = get_photo(found_id)

            for photo in photos:
                send_attachment(user_id, found_id, photo[0])

            vk_db.add_new_found(finder_id, found_id)
