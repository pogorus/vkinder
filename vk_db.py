import sqlalchemy
from data import db_name, db_password

engine = sqlalchemy.create_engine(f'postgresql://{db_name}:{db_password}@localhost:5432/vkinder')
connection = engine.connect()

def start_db():
    connection.execute(f'''create table if not exists Finder (
                                                vk_id varchar(20) primary key, 
                                                bdate varchar(10) not null, 
                                                sex integer not null,
                                                city integer not null,
                                                counter integer);''')

    connection.execute(f'''create table if not exists Found (
                                                vk_id varchar(20) primary key);''')

    connection.execute(f'''create table if not exists FinderFound (
                                                finder_id varchar(20) not null references Finder(vk_id),
                                                found_id varchar(20) not null references Found(vk_id),
                                                constraint finderfound_pk primary key (finder_id, found_id));''')


def get_finders_list():
    finders_vk_id = connection.execute('''SELECT vk_id FROM finder;''').fetchall()
    finders_list = []
    for finder in finders_vk_id:
        finders_list.append(finder[0])
    return finders_list


def get_bdate(finder_id):
    sql_bdate = connection.execute(f'''SELECT bdate FROM finder WHERE vk_id = '{finder_id}';''').fetchone()
    bdate = sql_bdate[0].split('.')
    return bdate


def get_sex(finder_id):
    sex = connection.execute(f'''SELECT sex FROM finder WHERE vk_id = '{finder_id}';''').fetchone()
    sex = sex[0]
    return sex


def get_city(finder_id):
    city = connection.execute(f'''SELECT city FROM finder WHERE vk_id = '{finder_id}';''').fetchone()
    city = city[0]
    return city


def get_counter(finder_id):
    counter = connection.execute(f'''SELECT counter FROM finder WHERE vk_id = '{finder_id}';''').fetchone()
    counter = counter[0]
    return counter


def add_new_finder(finder_id, bdate, sex, city):
    connection.execute(
        f'''INSERT INTO finder(vk_id, bdate, sex, city, counter) values ('{finder_id}', '{".".join(bdate)}', {sex}, {city}, 0);''')


def update_counter(finder_id):
    connection.execute(f'''UPDATE finder SET counter=counter+1 WHERE vk_id = '{finder_id}';''')


def add_new_found(finder_id, found_id):
    connection.execute(
        f'''INSERT INTO found(vk_id) values ('{found_id}');''')
    connection.execute(
        f'''INSERT INTO finderfound(finder_id, found_id) values ('{finder_id}', '{found_id}');''')
