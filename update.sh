sudo cp bot.conf /etc/supervisor/conf.d/cianbot.conf
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl status cian_bot
