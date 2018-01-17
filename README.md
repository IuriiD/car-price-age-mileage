# car-price-age-mileage / Correlating car's price, age and mileage - data from auto.ria.ua

My 1st real miniproject. Started on 01.11.2017 after learning Python/coding for ~175 hours (3-3.5months) in total, done in ~70 hours.
A Flask app that allows user to choose a car model and get scatter charts showing how this car's price is changing depending on its age and mileage.
Data is requested from <a href="https://auto.ria.com/">auto.ria.com</a> (the biggest Ukrainian advertisement board for vehicles) using their <a href="https://github.com/ria-com/auto-ria-rest-api">API</a>.
Charts (for age & price, price & mileage and age & mileage) are drawn using 2 charting engines/libraries - <a href="http://pygal.org/en/stable/index.html">pygal</a> and <a href="plot.ly">plot.ly</a>.
About 50% of time working on this miniproject was spent learning how to create a user management system in Flask (register, login, profile update, password update, password reset, avatar functions).
App has a preferences page (accessible for registered and logged in users) where a user can change 2 parameters: adverticements quantity for the model being analyzed (5-50) and the charting engine.
Topics learnt/covered in this project: Flask (including user management system), vagrant, git, virtualenv, REST API, requests, JSON parsing, charting (pygal, plot.ly), databases (MongoDB), bootstrap, deployment to server.
<div class="row">
        <div class="col">
          <a href="img/cpam-1.jpg" target="_blank"><img src="img/cpam-1.jpg" class="img-fluid img-thumbnail" style="max-width: 350px"></a>
        </div>
        <div class="col">
          <a href="img/cpam-2.jpg" target="_blank"><img src="img/cpam-2.jpg" class="img-fluid img-thumbnail" style="max-width: 350px"></a>
        </div>
        <div class="col">
          <a href="img/cpam-3.jpg" target="_blank"><img src="img/cpam-3.jpg" class="img-fluid img-thumbnail" style="max-width: 350px"></a>
        </div>
    </div>
</p>