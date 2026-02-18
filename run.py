import multiprocessing
import time
import bot
import dashboard


def run_bot():
    """Запуск бота в отдельном процессе"""
    bot.main()


def run_dashboard():
    """Запуск дашборда в отдельном процессе"""
    dashboard.run_dashboard()


if __name__ == '__main__':
    print("ЗАПУСК ПРОЕКТА")
    print(f"Бот: @Warehouse2026Bot")
    print(f"Дашборд: http://127.0.0.1:8050")
    print("Для остановки нажмите Ctrl+C")

    # Создание процессов
    bot_process = multiprocessing.Process(target=run_bot)
    dashboard_process = multiprocessing.Process(target=run_dashboard)

    try:
        # Запуск процессов
        bot_process.start()
        time.sleep(2)
        dashboard_process.start()

        # Ожидание завершения
        bot_process.join()
        dashboard_process.join()

    except KeyboardInterrupt:
        print("\nОСТАНОВКА ПРОЕКТА")

        # Завершение процессов
        bot_process.terminate()
        dashboard_process.terminate()
        bot_process.join()
        dashboard_process.join()

        print("Проект остановлен")