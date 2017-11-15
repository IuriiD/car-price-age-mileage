from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from pymongo import MongoClient
import pygal

app = Flask(__name__)
bootstrap = Bootstrap(app)

# Flask decorator, index page
@app.route('/')
def index():
    client = MongoClient()
    db = client.makemodels
    cll = db.cll
    mks = db.makes
    makes = []
    for doc in mks.find():
        makes.append(doc['make'])
    makes = sorted(makes)
    print(makes)
    '''makes = ['Abarth', 'Acura', 'Adler', 'Aero', 'Aixam', 'Alfa Romeo', 'Alpine', 'Altamarea', 'Armstrong Siddeley',
             'Aro', 'Artega', 'Asia', 'Aston Martin', 'Audi', 'Austin', 'Austin-Healey', 'Autobianchi', 'Avia', 'BMW',
             'BYD', 'Baoya', 'Barkas (Баркас)', 'Baw', 'Beijing', 'Bentley', 'Bertone', 'Bio Auto', 'Blonell',
             'Borgward', 'Brilliance', 'Bristol', 'Bugatti', 'Buick', 'Cadillac', 'Caterham', 'Chana', 'Changan',
             'Changhe', 'Chery', 'Chevrolet', 'Chrysler', 'Citroen', 'DAF / VDL', 'DKW', 'DS', 'Dacia', 'Dadi',
             'Daewoo', 'Daf', 'Dagger', 'Daihatsu', 'Daimler', 'Datsun', 'De Lorean', 'Derways', 'Detroit Electric',
             'Dfcz', 'Dodge', 'Dongfeng', 'Dr. Motor', 'Eagle', 'Ernst Auwarter', 'Estrima', 'FAW', 'FSO', 'FUQI',
             'Ferrari', 'Fiat', 'Fiat-Abarth', 'Fisker', 'Ford', 'Fornasari', 'GMC', 'Gac', 'Geely', 'Geo', 'Gonow',
             'Great Wall', 'Groz', 'Hafei', 'Haima', 'Hanomag', 'Hansa', 'Hindustan', 'Honda', 'Huabei', 'Huanghai',
             'Humber', 'Hummer', 'Humvee', 'Hyundai', 'Infiniti', 'Innocenti', 'Iran Khodro', 'Isuzu', 'ItalCar',
             'Iveco', 'JAC', 'JCB', 'JMC', 'Jaguar', 'Jeep', 'Jiangnan', 'Jinbei', 'Jinbei Minibusus', 'Jonway',
             'Karosa', 'Kia', 'King Long', 'KingWoo', 'Kirkham', 'Koenigsegg', 'Konecranes', 'LDV', 'LTI',
             'Lamborghini', 'Lancia', 'Land Rover', 'Landwind', 'Lexus', 'Lifan', 'Lincoln', 'Lotus', 'Luxgen', 'MEGA',
             'MG', 'MINI', 'MPM Motors', 'MYBRO', 'Marshell', 'Maruti', 'Maserati', 'Maybach', 'Mazda', 'McLaren',
             'Mercedes-Benz', 'Mercury', 'Merkur', 'Miles', 'Mitsubishi', 'Mitsuoka', 'Morgan', 'Morris', 'Nissan',
             'Norster', 'Nysa (Ныса)', 'Oldsmobile', 'Oltcit', 'Opel', 'Packard', 'Pagani', 'Peerless', 'Peg-Perego',
             'Peterbilt', 'Peugeot', 'Pininfarina', 'Pinzgauer', 'Plymouth', 'Pontiac', 'Porsche', 'Praga Baby',
             'Proton', 'Quicksilver', 'Ram', 'Ravon', 'Renault', 'Renault Samsung Motors', 'Rezvani', 'Rimac',
             'Rolls-Royce', 'Rover', 'SMA', 'Saab', 'Saipa', 'Saleen', 'Samand', 'Samson', 'Samsung', 'Saturn', 'Sceo',
             'Scion', 'Seat', 'Secma', 'Selena', 'Shelby', 'Shuanghuan', 'Sidetracker', 'Skoda', 'Smart', 'SouEast',
             'Soyat', 'Spyker', 'SsangYong', 'Star', 'Studebaker', 'Subaru', 'Sunbeam', 'Suzuki', 'TATA', 'TVR',
             'Talbot', 'Tarpan Honker', 'Tatra', 'Tazzari', 'Tesla', 'Think Global', 'Thunder Tiger', 'Tianma', 'Tiger',
             'Tofas', 'Toyota', 'Trabant', 'Triumph', 'Ultima', 'Van Hool', 'Vauxhall', 'Venturi', 'Vepr', 'Volkswagen',
             'Volvo', 'Wanderer', 'Wanfeng', 'Wartburg', 'Wiesmann', 'Willys', 'Wuling', 'Xiaolong', 'Xin kai', 'Yugo',
             'ZX', 'Zastava', 'Zimmer', 'Zotye', 'Zuk', 'Богдан', 'Бронто', 'ВАЗ', 'ВИС', 'ГАЗ', 'ГолАЗ',
             'Детский транспорт', 'Другое', 'ЕРАЗ', 'Жук', 'ЗАЗ', 'ЗИЛ', 'ЗИМ', 'ЗИС', 'ИЖ', 'ЛуАЗ', 'Москвич / АЗЛК',
             'Прицеп', 'РАФ', 'Ретро автомобили', 'СМЗ', 'СПЭВ / SPEV', 'Самодельный', 'СеАЗ', 'ТАМ', 'ТагАЗ', 'ТогАЗ',
             'Тренер', 'УАЗ', 'Циклон', 'Эстония']'''
    makemodellist = []
    for make in makes:
        models4make = []
        for doc in cll.find({'make': make}):
            models4make.append('/' + doc['make'] + '/' + doc['model'])
        makemodellist.append([make, sorted(models4make)])
        makemodellist = sorted(makemodellist)
    #print(makemodellist)
    return render_template('index.html', makemodellist=makemodellist)
##
# Run Flask server (host='0.0.0.0' - for Vagrant)
if __name__ == '__main__':
    app.run(host='0.0.0.0',debug=True)

