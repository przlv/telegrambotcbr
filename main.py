from app import TelegramBot
from config import TOKEN


if __name__ == '__main__':
    
    bot = TelegramBot(TOKEN)
    
    bot.run()
