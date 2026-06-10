import requests

class UploadStaticFiles:
    def __init__(self):
        self.url = "http://192.168.252.164:9111/static_files.php"

    def fetch_data(self):
        """Получает данные с сервера."""
        try:
            response = requests.get(self.url)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Ошибка получения данных: {e}")
            return []

    def get_data_as_list(self):
        """Возвращает данные в виде массива строк."""
        data = self.fetch_data()
        return data  # Возвращаем массив данных
