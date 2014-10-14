DEBUG = False

DATABASE_USER = ''
DATABASE_PASSWORD = ''
DATABASE_HOST = 'localhost'
DATABASE_PORT = 5432
DATABASE_NAME = 'icingaidoutils'

DATABASE_URL="postgresql://{}:{}@{}/{}".format(DATABASE_USER,
                                               DATABASE_PASSWORD,
                                               DATABASE_HOST,
                                               DATABASE_NAME)