#!/bin/bash

# ============================================
# ЕДИНЫЙ УСТАНОВОЧНЫЙ СКРИПТ KSB_SG
# ============================================

# Замените эти значения на реальные имя пользователя и пароль
USERNAME="ksb"
PASSWORD="123456"

# Новые пути в каталоге /opt
TARGET_DIR="/opt/KSB_SG"
APP_PATH="$TARGET_DIR/bin/main"
WORKING_DIR="$TARGET_DIR/bin"
ICON_PATH="$TARGET_DIR/ksb.ico"

# Пути к дополнительному ПО
REMOTE_SOFT_DIR="$TARGET_DIR/remote_soft"
NOMACHINE_DEB="$REMOTE_SOFT_DIR/nomachine.deb"
ASSISTANT_RPM="$REMOTE_SOFT_DIR/assistent.rpm"
ASSISTANT_DEB="$REMOTE_SOFT_DIR/assistent.deb"

# Укажите путь к ZIP-архиву
ZIP_FILE="KSB_SG.zip"

# Создание целевой директории в /opt с правами
echo $PASSWORD | sudo -S mkdir -p "$TARGET_DIR"
echo $PASSWORD | sudo -S chown -R $USERNAME:$USERNAME "$TARGET_DIR"
echo $PASSWORD | sudo -S chmod -R 755 "$TARGET_DIR"

# Разархивирование ZIP-архива в целевую директорию
unzip -o "$ZIP_FILE" -d "$TARGET_DIR"

# Устанавливаем права на все файлы в каталоге (включая remote_soft)
echo $PASSWORD | sudo -S chown -R $USERNAME:$USERNAME "$TARGET_DIR"
echo $PASSWORD | sudo -S chmod -R 755 "$TARGET_DIR"
echo $PASSWORD | sudo -S chmod +x "$APP_PATH" 2>/dev/null || true

# Создаем папку remote_soft если её нет и устанавливаем права
mkdir -p "$REMOTE_SOFT_DIR"
echo $PASSWORD | sudo -S chown -R $USERNAME:$USERNAME "$REMOTE_SOFT_DIR"
echo $PASSWORD | sudo -S chmod -R 755 "$REMOTE_SOFT_DIR"

# === УСТАНОВКА ДОПОЛНИТЕЛЬНОГО ПО ===

echo "=== УСТАНОВКА ДОПОЛНИТЕЛЬНОГО ПО ==="

# Функция для проверки наличия файла
check_file() {
    if [ ! -f "$1" ]; then
        echo "⚠️ Файл не найден: $1"
        return 1
    else
        echo "✅ Найден файл: $1"
        return 0
    fi
}

# Установка NoMachine
if check_file "$NOMACHINE_DEB"; then
    echo "Установка NoMachine..."
    echo $PASSWORD | sudo -S dpkg -i "$NOMACHINE_DEB" || {
        echo "Установка зависимостей для NoMachine..."
        echo $PASSWORD | sudo -S apt-get install -f -y
    }
    echo "✅ NoMachine установлен"
else
    echo "❌ NoMachine не установлен (файл не найден)"
fi

# Установка Ассистент (проверяем оба формата)
if check_file "$ASSISTANT_DEB"; then
    echo "Установка Ассистент (DEB)..."
    echo $PASSWORD | sudo -S dpkg -i "$ASSISTANT_DEB" || {
        echo "Установка зависимостей для Ассистент..."
        echo $PASSWORD | sudo -S apt-get install -f -y
    }
    echo "✅ Ассистент установлен"
elif check_file "$ASSISTANT_RPM"; then
    echo "Установка Ассистент (RPM)..."
    if command -v alien &> /dev/null; then
        echo "Конвертация RPM в DEB..."
        echo $PASSWORD | sudo -S alien -k "$ASSISTANT_RPM"
        CONVERTED_DEB=$(find . -name "*.deb" -type f | head -1)
        if [ -n "$CONVERTED_DEB" ]; then
            echo $PASSWORD | sudo -S dpkg -i "$CONVERTED_DEB" || {
                echo $PASSWORD | sudo -S apt-get install -f -y
            }
            echo "✅ Ассистент установлен через конвертацию"
        else
            echo "❌ Ошибка конвертации RPM в DEB"
        fi
    else
        echo "Установка alien для конвертации RPM..."
        echo $PASSWORD | sudo -S apt-get install -y alien
        echo $PASSWORD | sudo -S alien -k "$ASSISTANT_RPM"
        CONVERTED_DEB=$(find . -name "*.deb" -type f | head -1)
        if [ -n "$CONVERTED_DEB" ]; then
            echo $PASSWORD | sudo -S dpkg -i "$CONVERTED_DEB" || {
                echo $PASSWORD | sudo -S apt-get install -f -y
            }
            echo "✅ Ассистент установлен через конвертацию"
        else
            echo "❌ Ошибка конвертации RPM в DEB"
        fi
    fi
else
    echo "❌ Ассистент не установлен (файлы .deb или .rpm не найдены)"
fi

# === СОЗДАНИЕ INI КОНФИГУРАЦИОННОГО ФАЙЛА ===

echo "=== СОЗДАНИЕ КОНФИГУРАЦИИ ==="

# Создаем INI файл конфигурации
CONFIG_INI="$TARGET_DIR/reboot_config.ini"
cat > $CONFIG_INI << 'EOF'
; Конфигурация автоматической перезагрузки системы
; Формат: INI файл
; Версия конфигурации: 1.0

[Reboot]
; Режим перезагрузки:
; periodic - перезагрузка с заданным интервалом
; scheduled - перезагрузка по расписанию
; disabled - автоперезагрузка отключена
mode = periodic

; Параметры для периодического режима (mode = periodic)
; Интервал перезагрузки в часах (1-168)
interval_hours = 24

; Параметры для режима по расписанию (mode = scheduled)
; Время перезагрузки в формате HH:MM (можно указать несколько через запятую)
; Пример: 02:00 - одна перезагрузка
; Пример: 02:00,14:00 - две перезагрузки
; Пример: 00:00,06:00,12:00,18:00 - каждые 6 часов
reboot_times = 02:00

; Общие настройки
; Минимальное время работы системы перед перезагрузкой (часы)
min_uptime_hours = 1

; Включить логирование (yes/no)
logging_enabled = yes

; Путь к лог-файлу
log_file = /var/log/auto_reboot.log

; Автоматически перезагружать службу при изменении конфигурации (yes/no)
auto_reload_config = yes
EOF

echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME $CONFIG_INI

# === СОЗДАНИЕ СКРИПТА АВТОМАТИЧЕСКОЙ ПЕРЕЗАГРУЗКИ С ОТСЛЕЖИВАНИЕМ ИЗМЕНЕНИЙ ===

echo "=== СОЗДАНИЕ СЛУЖБЫ АВТОПЕРЕЗАГРУЗКИ ==="

# Создаем основной скрипт автоперезагрузки
REBOOT_SCRIPT="$TARGET_DIR/auto_reboot.sh"
cat > $REBOOT_SCRIPT << 'EOF'
#!/bin/bash

# Скрипт автоматической перезагрузки
CONFIG_FILE="/opt/KSB_SG/reboot_config.ini"
CONFIG_MD5_FILE="/var/run/reboot_config.md5"
SERVICE_NAME="auto_reboot.service"

# Функция чтения значения из INI файла
read_ini() {
    local section=$1
    local key=$2
    local value=""

    value=$(awk -F '=' -v section="[$section]" -v key="$key" '
        $0 == section { in_section=1; next }
        /^\[/ { in_section=0 }
        in_section && $1 ~ key {
            gsub(/^[ \t]+|[ \t]+$/, "", $2)
            print $2
            exit
        }
    ' "$CONFIG_FILE")

    echo "$value"
}

# Функция логирования
log_message() {
    local logging_enabled=$(read_ini "Reboot" "logging_enabled")
    if [ "$logging_enabled" = "yes" ]; then
        local log_file=$(read_ini "Reboot" "log_file")
        echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$log_file"
    fi
}

# Функция проверки изменения конфигурации
check_config_changed() {
    if [ ! -f "$CONFIG_FILE" ]; then
        return 1
    fi

    local current_md5=$(md5sum "$CONFIG_FILE" | cut -d' ' -f1)
    local saved_md5=""

    if [ -f "$CONFIG_MD5_FILE" ]; then
        saved_md5=$(cat "$CONFIG_MD5_FILE")
    fi

    if [ "$current_md5" != "$saved_md5" ]; then
        echo "$current_md5" > "$CONFIG_MD5_FILE"
        return 0  # Конфигурация изменилась
    fi
    return 1  # Конфигурация не изменилась
}

# Функция перезагрузки службы
reload_service() {
    log_message "Обнаружено изменение конфигурации. Перезагрузка службы..."

    # Отправляем сигнал родительскому процессу для перезапуска
    if systemctl is-active --quiet "$SERVICE_NAME"; then
        systemctl restart "$SERVICE_NAME"
        log_message "Служба перезагружена"
    else
        log_message "Служба не активна, перезапуск не требуется"
    fi

    # Завершаем текущий процесс (будет перезапущен systemd)
    exit 0
}

# Функция проверки uptime
check_uptime() {
    local min_uptime=$(read_ini "Reboot" "min_uptime_hours")
    local uptime_seconds=$(awk '{print $1}' /proc/uptime | cut -d. -f1)
    local uptime_hours=$((uptime_seconds / 3600))

    if [ $uptime_hours -lt $min_uptime ]; then
        log_message "Система работает менее $min_uptime часов ($uptime_hours ч). Перезагрузка отложена"
        return 1
    fi
    return 0
}

# Функция выполнения перезагрузки
perform_reboot() {
    local reboot_reason="$1"

    log_message "ВЫПОЛНЕНИЕ ПЕРЕЗАГРУЗКИ: $reboot_reason"
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Перезагрузка: $reboot_reason" > /var/run/last_auto_reboot

    # Выполняем перезагрузку
    /sbin/shutdown -r now
}

# Функция для периодического режима
check_periodic_reboot() {
    local interval_hours=$(read_ini "Reboot" "interval_hours")
    local last_reboot_file="/var/run/last_auto_reboot"
    local last_reboot_time=0
    local current_time=$(date +%s)

    if [ -f "$last_reboot_file" ]; then
        last_reboot_time=$(grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\} [0-9]\{2\}:[0-9]\{2\}:[0-9]\{2\}' "$last_reboot_file" | head -1 | xargs -I {} date -d "{}" +%s 2>/dev/null)
        [ -z "$last_reboot_time" ] && last_reboot_time=0
    fi

    local time_since_last_reboot=$((current_time - last_reboot_time))
    local interval_seconds=$((interval_hours * 3600))

    if [ $time_since_last_reboot -ge $interval_seconds ]; then
        if check_uptime; then
            perform_reboot "Истек интервал перезагрузки ($interval_hours часов)"
            return 0
        fi
    fi
    return 1
}

# Функция для режима по расписанию
check_scheduled_reboot() {
    local reboot_times=$(read_ini "Reboot" "reboot_times")
    local current_hour=$(date +%H)
    local current_minute=$(date +%M)
    local current_time="$current_hour:$current_minute"
    local current_date=$(date +%Y-%m-%d)
    local last_reboot_file="/var/run/last_auto_reboot"
    local last_reboot_date=""

    if [ -f "$last_reboot_file" ]; then
        last_reboot_date=$(grep -o '[0-9]\{4\}-[0-9]\{2\}-[0-9]\{2\}' "$last_reboot_file" | head -1)
    fi

    # Разбиваем времена на массив
    IFS=',' read -ra TIMES_ARRAY <<< "$reboot_times"

    for scheduled_time in "${TIMES_ARRAY[@]}"; do
        scheduled_time=$(echo "$scheduled_time" | xargs)

        if [ "$current_time" = "$scheduled_time" ]; then
            if [ "$last_reboot_date" != "$current_date" ]; then
                if check_uptime; then
                    perform_reboot "Запланированная перезагрузка в $scheduled_time"
                    return 0
                fi
            else
                log_message "Перезагрузка в $scheduled_time уже выполнялась сегодня"
            fi
            break
        fi
    done
    return 1
}

# Основной цикл с отслеживанием изменений конфигурации
main() {
    # Проверяем существование конфигурации
    if [ ! -f "$CONFIG_FILE" ]; then
        echo "Ошибка: Файл конфигурации не найден: $CONFIG_FILE"
        exit 1
    fi

    # Сохраняем начальную MD5 конфигурации
    if [ -f "$CONFIG_FILE" ]; then
        md5sum "$CONFIG_FILE" | cut -d' ' -f1 > "$CONFIG_MD5_FILE"
    fi

    local mode=$(read_ini "Reboot" "mode")
    local auto_reload=$(read_ini "Reboot" "auto_reload_config")

    log_message "Служба автоперезагрузки запущена. Режим: $mode"
    log_message "Автоматическая перезагрузка при изменении конфига: $auto_reload"

    local check_counter=0

    while true; do
        # Проверяем изменение конфигурации каждые 30 секунд
        if [ "$auto_reload" = "yes" ]; then
            if check_config_changed; then
                log_message "Обнаружено изменение конфигурации"
                reload_service
                # После reload_service скрипт завершится и будет перезапущен systemd
                return
            fi
        fi

        # Проверяем необходимость перезагрузки
        case "$mode" in
            periodic)
                check_periodic_reboot
                ;;
            scheduled)
                check_scheduled_reboot
                ;;
            disabled)
                # Ничего не делаем
                ;;
            *)
                log_message "Неизвестный режим: $mode"
                ;;
        esac

        # Обновляем режим на случай если он изменился в конфиге
        mode=$(read_ini "Reboot" "mode")

        sleep 60
    done
}

main
EOF

chmod +x $REBOOT_SCRIPT
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME $REBOOT_SCRIPT

# === СОЗДАНИЕ SYSTEMD СЛУЖБЫ ===

REBOOT_SERVICE="auto_reboot.service"
REBOOT_SERVICE_PATH="/etc/systemd/system/$REBOOT_SERVICE"

echo $PASSWORD | sudo -S bash -c "cat > $REBOOT_SERVICE_PATH" <<EOL
[Unit]
Description=Automatic System Reboot Service
After=network.target
After=multi-user.target

[Service]
Type=simple
ExecStart=$REBOOT_SCRIPT
Restart=always
RestartSec=10
User=$USERNAME
KillMode=process

[Install]
WantedBy=multi-user.target
EOL

# Включаем и запускаем службу
echo $PASSWORD | sudo -S systemctl daemon-reload
echo $PASSWORD | sudo -S systemctl enable $REBOOT_SERVICE
echo $PASSWORD | sudo -S systemctl start $REBOOT_SERVICE

# === СОЗДАНИЕ СКРИПТА УПРАВЛЕНИЯ ===

CONTROL_SCRIPT="$TARGET_DIR/control_reboot.sh"
cat > $CONTROL_SCRIPT << 'EOF'
#!/bin/bash

CONFIG_FILE="/opt/KSB_SG/reboot_config.ini"
SERVICE_NAME="auto_reboot.service"

# Функция отображения меню
show_menu() {
    clear
    echo "========================================="
    echo "   УПРАВЛЕНИЕ АВТОПЕРЕЗАГРУЗКОЙ"
    echo "========================================="
    echo ""
    echo "1. Показать текущую конфигурацию"
    echo "2. Изменить режим на ПЕРИОДИЧЕСКИЙ"
    echo "3. Изменить режим на ПО РАСПИСАНИЮ"
    echo "4. Изменить режим на ОТКЛЮЧЕН"
    echo "5. Изменить интервал (периодический режим)"
    echo "6. Изменить время расписания"
    echo "7. Перезапустить службу вручную"
    echo "8. Показать статус и логи"
    echo "9. Выйти"
    echo ""
    read -p "Выберите пункт [1-9]: " choice

    case $choice in
        1) show_config ;;
        2) set_mode "periodic" ;;
        3) set_mode "scheduled" ;;
        4) set_mode "disabled" ;;
        5) set_interval ;;
        6) set_times ;;
        7) manual_restart ;;
        8) show_status ;;
        9) exit 0 ;;
        *) echo "Неверный выбор"; sleep 2; show_menu ;;
    esac
}

# Показать конфигурацию
show_config() {
    clear
    echo "=== ТЕКУЩАЯ КОНФИГУРАЦИЯ ==="
    echo ""
    cat "$CONFIG_FILE"
    echo ""
    read -p "Нажмите Enter для продолжения..."
    show_menu
}

# Перезапуск службы
restart_service() {
    echo "Перезапуск службы автоперезагрузки..."
    sudo systemctl restart $SERVICE_NAME
    echo "✅ Служба перезапущена"

    sleep 2
    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "✅ Служба успешно запущена"
    else
        echo "❌ Ошибка при запуске службы"
    fi
}

# Установить режим
set_mode() {
    local mode=$1
    local mode_text=""

    case $mode in
        periodic) mode_text="Периодический (каждые X часов)" ;;
        scheduled) mode_text="По расписанию (в указанное время)" ;;
        disabled) mode_text="Отключен" ;;
    esac

    echo "Установка режима: $mode_text"
    sudo sed -i "s/^mode = .*/mode = $mode/" "$CONFIG_FILE"
    echo "✅ Режим изменен на: $mode_text"

    auto_reload=$(grep "^auto_reload_config" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
    if [ "$auto_reload" = "yes" ]; then
        echo "🔄 Служба автоматически перезагрузится через несколько секунд"
        sleep 3
    else
        read -p "Перезапустить службу сейчас? (y/n): " restart
        if [ "$restart" = "y" ]; then
            restart_service
        fi
    fi

    sleep 2
    show_menu
}

# Установить интервал
set_interval() {
    clear
    echo "=== НАСТРОЙКА ИНТЕРВАЛА ==="
    echo ""
    echo "Выберите интервал перезагрузки:"
    echo "1. Раз в сутки (24 часа)"
    echo "2. Дважды в сутки (12 часов)"
    echo "3. Трижды в сутки (8 часов)"
    echo "4. Каждые 6 часов"
    echo "5. Каждые 4 часа"
    echo "6. Каждые 2 часа"
    echo "7. Каждый час"
    echo "8. Свой вариант"
    read -p "Выберите пункт [1-8]: " choice

    case $choice in
        1) interval=24 ;;
        2) interval=12 ;;
        3) interval=8 ;;
        4) interval=6 ;;
        5) interval=4 ;;
        6) interval=2 ;;
        7) interval=1 ;;
        8) read -p "Введите интервал в часах (1-168): " interval ;;
        *) echo "Неверный выбор"; set_interval; return ;;
    esac

    if [ "$interval" -ge 1 ] && [ "$interval" -le 168 ]; then
        sudo sed -i "s/^interval_hours = .*/interval_hours = $interval/" "$CONFIG_FILE"
        sudo sed -i "s/^mode = .*/mode = periodic/" "$CONFIG_FILE"
        echo "✅ Интервал установлен: $interval часов"
        echo "✅ Режим автоматически установлен на 'periodic'"

        auto_reload=$(grep "^auto_reload_config" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
        if [ "$auto_reload" = "yes" ]; then
            echo "🔄 Служба автоматически перезагрузится через несколько секунд"
            sleep 3
        else
            read -p "Перезапустить службу сейчас? (y/n): " restart
            if [ "$restart" = "y" ]; then
                restart_service
            fi
        fi
    else
        echo "❌ Неверный интервал (должен быть от 1 до 168)"
        sleep 2
        set_interval
    fi

    sleep 2
    show_menu
}

# Установить время расписания
set_times() {
    clear
    echo "=== НАСТРОЙКА РАСПИСАНИЯ ==="
    echo ""
    echo "Введите время перезагрузки в формате HH:MM"
    echo "Можно указать несколько времен через запятую"
    echo "Примеры:"
    echo "  02:00 - одна перезагрузка"
    echo "  02:00,14:00 - две перезагрузки"
    echo "  00:00,06:00,12:00,18:00 - каждые 6 часов"
    echo ""
    read -p "Время(а) перезагрузки: " times

    if [ -n "$times" ]; then
        sudo sed -i "s/^reboot_times = .*/reboot_times = $times/" "$CONFIG_FILE"
        sudo sed -i "s/^mode = .*/mode = scheduled/" "$CONFIG_FILE"
        echo "✅ Расписание установлено: $times"
        echo "✅ Режим автоматически установлен на 'scheduled'"

        auto_reload=$(grep "^auto_reload_config" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
        if [ "$auto_reload" = "yes" ]; then
            echo "🔄 Служба автоматически перезагрузится через несколько секунд"
            sleep 3
        else
            read -p "Перезапустить службу сейчас? (y/n): " restart
            if [ "$restart" = "y" ]; then
                restart_service
            fi
        fi
    else
        echo "❌ Время не указано"
        sleep 2
        set_times
    fi

    sleep 2
    show_menu
}

# Ручная перезагрузка службы
manual_restart() {
    restart_service
    read -p "Нажмите Enter для продолжения..."
    show_menu
}

# Показать статус
show_status() {
    clear
    echo "=== СТАТУС АВТОПЕРЕЗАГРУЗКИ ==="
    echo ""

    if systemctl is-active --quiet $SERVICE_NAME; then
        echo "Служба: ✅ АКТИВНА"
    else
        echo "Служба: ❌ НЕ АКТИВНА"
    fi

    if systemctl is-enabled --quiet $SERVICE_NAME; then
        echo "Автозапуск: ✅ ВКЛЮЧЕН"
    else
        echo "Автозапуск: ❌ ОТКЛЮЧЕН"
    fi

    echo ""
    echo "Текущий режим:"
    grep "^mode" "$CONFIG_FILE"

    echo ""
    echo "Параметры:"
    grep -E "^(interval_hours|reboot_times|auto_reload_config)=" "$CONFIG_FILE"

    echo ""
    echo "Последние записи в логе:"
    LOG_FILE=$(grep "^log_file" "$CONFIG_FILE" | cut -d'=' -f2 | xargs)
    if [ -f "$LOG_FILE" ]; then
        tail -n 15 "$LOG_FILE"
    else
        echo "Лог-файл не найден или логирование отключено"
    fi

    echo ""
    read -p "Нажмите Enter для продолжения..."
    show_menu
}

# Запуск меню
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Ошибка: Файл конфигурации не найден: $CONFIG_FILE"
    exit 1
fi

show_menu
EOF

chmod +x $CONTROL_SCRIPT
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME $CONTROL_SCRIPT

# === СОЗДАНИЕ СКРИПТА ПЕРЕУСТАНОВКИ ===

REINSTALL_SOFTWARE_SCRIPT="$TARGET_DIR/reinstall_additional_software.sh"
cat > $REINSTALL_SOFTWARE_SCRIPT << 'EOF'
#!/bin/bash

USERNAME="ksb"
PASSWORD="123456"
REMOTE_SOFT_DIR="/opt/KSB_SG/remote_soft"
NOMACHINE_DEB="$REMOTE_SOFT_DIR/nomachine.deb"
ASSISTANT_RPM="$REMOTE_SOFT_DIR/assistent.rpm"
ASSISTANT_DEB="$REMOTE_SOFT_DIR/assistent.deb"

echo "=== ПЕРЕУСТАНОВКА ДОПОЛНИТЕЛЬНОГО ПО ==="

check_file() {
    if [ ! -f "$1" ]; then
        echo "⚠️ Файл не найден: $1"
        return 1
    else
        echo "✅ Найден файл: $1"
        return 0
    fi
}

if check_file "$NOMACHINE_DEB"; then
    echo "Переустановка NoMachine..."
    sudo dpkg -r nomachine 2>/dev/null || true
    sudo dpkg -i "$NOMACHINE_DEB" || {
        sudo apt-get install -f -y
    }
    echo "✅ NoMachine переустановлен"
else
    echo "❌ NoMachine не переустановлен (файл не найден)"
fi

if check_file "$ASSISTANT_DEB"; then
    echo "Переустановка Ассистент (DEB)..."
    sudo dpkg -r ассистент 2>/dev/null || true
    sudo dpkg -i "$ASSISTANT_DEB" || {
        sudo apt-get install -f -y
    }
    echo "✅ Ассистент переустановлен"
elif check_file "$ASSISTANT_RPM"; then
    echo "Переустановка Ассистент (RPM)..."
    if command -v alien &> /dev/null; then
        sudo alien -k "$ASSISTANT_RPM"
        CONVERTED_DEB=$(find . -name "*.deb" -type f | head -1)
        if [ -n "$CONVERTED_DEB" ]; then
            sudo dpkg -i "$CONVERTED_DEB" || {
                sudo apt-get install -f -y
            }
            echo "✅ Ассистент переустановлен через конвертацию"
        else
            echo "❌ Ошибка конвертации RPM в DEB"
        fi
    else
        echo "❌ Alien не установлен, невозможно конвертировать RPM"
    fi
else
    echo "❌ Ассистент не переустановлен (файлы не найдены)"
fi

echo "=== ПЕРЕУСТАНОВКА ЗАВЕРШЕНА ==="
read -p "Нажмите Enter для закрытия..."
EOF

chmod +x $REINSTALL_SOFTWARE_SCRIPT
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME $REINSTALL_SOFTWARE_SCRIPT

# === ОТКЛЮЧЕНИЕ АВТОМАТИЧЕСКИХ ОБНОВЛЕНИЙ ===

echo "=== ОТКЛЮЧЕНИЕ АВТООБНОВЛЕНИЙ ==="

# Останавливаем и отключаем автоматические службы обновлений
echo $PASSWORD | sudo -S systemctl stop unattended-upgrades 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl disable unattended-upgrades 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl stop apt-daily.timer 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl disable apt-daily.timer 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl stop apt-daily-upgrade.timer 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl disable apt-daily-upgrade.timer 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl stop apt-daily.service 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl disable apt-daily.service 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl stop apt-daily-upgrade.service 2>/dev/null || true
echo $PASSWORD | sudo -S systemctl disable apt-daily-upgrade.service 2>/dev/null || true

# Отключаем автоматические проверки обновлений через apt
echo $PASSWORD | sudo -S bash -c 'cat > /etc/apt/apt.conf.d/99disable-auto-updates' << 'EOF'
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APT::Periodic::Unattended-Upgrade "0";
APT::Periodic::Enable "0";
EOF

echo $PASSWORD | sudo -S bash -c 'cat > /etc/apt/apt.conf.d/20auto-upgrades' << 'EOF'
APT::Periodic::Update-Package-Lists "0";
APT::Periodic::Download-Upgradeable-Packages "0";
APT::Periodic::AutocleanInterval "0";
APT::Periodic::Unattended-Upgrade "0";
EOF

# Отключаем уведомления о обновлениях в GNOME
gsettings set org.gnome.software download-updates false
gsettings set org.gnome.software allow-updates false
gsettings set com.ubuntu.update-notifier no-show-notifications true

# Удаляем пакеты уведомлений
echo $PASSWORD | sudo -S apt-get remove update-notifier update-manager -y 2>/dev/null || true
echo $PASSWORD | sudo -S apt-get purge update-notifier update-manager -y 2>/dev/null || true
echo $PASSWORD | sudo -S apt-mark hold update-notifier update-manager ubuntu-release-upgrader-core 2>/dev/null || true

# Отключаем snap обновления
if command -v snap &> /dev/null; then
    echo $PASSWORD | sudo -S snap set system refresh.hold="2030-01-01T00:00:00Z"
fi

# Удаляем cron задачи
(sudo crontab -l 2>/dev/null | grep -v 'apt.*update' | grep -v 'unattended-upgrade') | sudo crontab - 2>/dev/null || true
(crontab -l 2>/dev/null | grep -v 'update') | crontab - 2>/dev/null || true

# Отключаем flatpak обновления
if command -v flatpak &> /dev/null; then
    flatpak remote-modify --no-auto-deploy flathub
    flatpak remote-modify --no-auto-deploy ubuntu
fi

# === НАСТРОЙКА АВТОЗАПУСКА ПРИЛОЖЕНИЯ ===

echo "=== НАСТРОЙКА АВТОЗАПУСКА ==="

mkdir -p ~/.config/autostart
echo "[Desktop Entry]
Type=Application
Exec=$APP_PATH --fullscreen
Path=$WORKING_DIR
Name=ksb
Icon=$ICON_PATH
Terminal=false
X-GNOME-Autostart-enabled=true" > ~/.config/autostart/myapp.desktop

# Установка необходимых пакетов
echo $PASSWORD | sudo -S apt-get update
echo $PASSWORD | sudo -S apt-get install -y anki rhvoice rhvoice-english rhvoice-russian lame xsltproc ffmpeg nmap mplayer portaudio19-dev x11-xserver-utils lm-sensors acpi

# Создаем ярлык на рабочем столе для приложения
echo "[Desktop Entry]
Type=Application
Exec=$APP_PATH
Path=$WORKING_DIR
Name=ksb
Icon=$ICON_PATH
Terminal=false" > /tmp/myapp.desktop

echo $PASSWORD | sudo -S mv /tmp/myapp.desktop /home/ksb/Desktop/
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME /home/ksb/Desktop/myapp.desktop
echo $PASSWORD | sudo -S chmod +x /home/ksb/Desktop/myapp.desktop

# === ОТКЛЮЧЕНИЕ ЭНЕРГОСБЕРЕЖЕНИЯ ===

echo "=== ОТКЛЮЧЕНИЕ ЭНЕРГОСБЕРЕЖЕНИЯ ==="

gsettings set org.gnome.desktop.session idle-delay 0
gsettings set org.gnome.desktop.screensaver idle-activation-enabled false
gsettings set org.gnome.desktop.screensaver lock-enabled false
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-timeout 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-display-ac 0
gsettings set org.gnome.settings-daemon.plugins.power sleep-display-battery 0
gsettings set org.gnome.settings-daemon.plugins.power power-button-action 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-ac-type 'nothing'
gsettings set org.gnome.settings-daemon.plugins.power sleep-inactive-battery-type 'nothing'

xset -dpms
xset s off

# === НАСТРОЙКА ПОВЕДЕНИЯ ПРИ ЗАКРЫТИИ КРЫШКИ ===

echo "=== НАСТРОЙКА ЗАКРЫТИЯ КРЫШКИ ==="

echo $PASSWORD | sudo -S cp /etc/systemd/logind.conf /etc/systemd/logind.conf.backup
echo $PASSWORD | sudo -S sed -i 's/^#HandleLidSwitch=.*/HandleLidSwitch=ignore/' /etc/systemd/logind.conf
echo $PASSWORD | sudo -S sed -i 's/^#HandleLidSwitchExternalPower=.*/HandleLidSwitchExternalPower=ignore/' /etc/systemd/logind.conf
echo $PASSWORD | sudo -S sed -i 's/^#HandleLidSwitchDocked=.*/HandleLidSwitchDocked=ignore/' /etc/systemd/logind.conf
echo $PASSWORD | sudo -S systemctl restart systemd-logind

# === НАСТРОЙКА РАСКЛАДКИ КЛАВИАТУРЫ ===

echo "=== НАСТРОЙКА КЛАВИАТУРЫ ==="

echo $PASSWORD | sudo -S apt-get install -y language-pack-ru
gsettings set org.gnome.desktop.input-sources sources "[('xkb', 'us'), ('xkb', 'ru')]"
gsettings set org.gnome.desktop.wm.keybindings switch-input-source "['<Alt>Shift_L', '<Alt>Shift_R']"
gsettings set org.gnome.desktop.wm.keybindings switch-input-source-backward "['<Shift>Alt_L', '<Shift>Alt_R']"
setxkbmap -layout us,ru -option grp:alt_shift_toggle

KEYBOARD_SCRIPT="/home/ksb/set_keyboard.sh"
cat > $KEYBOARD_SCRIPT << 'EOF'
#!/bin/bash
setxkbmap -layout us,ru -option grp:alt_shift_toggle
EOF

chmod +x $KEYBOARD_SCRIPT

echo "[Desktop Entry]
Type=Application
Exec=$KEYBOARD_SCRIPT
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=Keyboard Setup
Comment=Set up keyboard layout and switching" > ~/.config/autostart/keyboard-setup.desktop

# === УСТАНОВКА СЛУЖБЫ ДЛЯ LAPTOP_MONITOR.SH ===

echo "=== УСТАНОВКА LAPTOP_MONITOR СЛУЖБЫ ==="

SCRIPT_PATH="$TARGET_DIR/sh/laptop_monitor.sh"

if [ ! -f "$SCRIPT_PATH" ]; then
    echo "Создание скрипта-заглушки laptop_monitor.sh"
    mkdir -p "$TARGET_DIR/sh"
    cat > "$SCRIPT_PATH" << 'EOF'
#!/bin/bash
while true; do
    sleep 60
done
EOF
    chmod +x "$SCRIPT_PATH"
fi

chmod +x "$SCRIPT_PATH"

SERVICE_NAME="laptop_monitor.service"
SERVICE_PATH="/etc/systemd/system/$SERVICE_NAME"

echo $PASSWORD | sudo -S bash -c "cat > $SERVICE_PATH" <<EOL
[Unit]
Description=Laptop Monitor Service
After=network.target

[Service]
ExecStart=$SCRIPT_PATH
Restart=always
User=$USERNAME

[Install]
WantedBy=multi-user.target
EOL

echo $PASSWORD | sudo -S systemctl daemon-reload

# === СОЗДАНИЕ ЯРЛЫКОВ НА РАБОЧЕМ СТОЛЕ ===

echo "=== СОЗДАНИЕ ЯРЛЫКОВ ==="

# Ярлык для управления автоперезагрузкой
echo "[Desktop Entry]
Type=Application
Exec=gnome-terminal -- bash -c 'sudo $CONTROL_SCRIPT'
Name=Управление автоперезагрузкой
Comment=Настройка автоматической перезагрузки системы
Icon=system-reboot
Terminal=false
Categories=System;" > /home/ksb/Desktop/reboot-control.desktop

chmod +x /home/ksb/Desktop/reboot-control.desktop
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME /home/ksb/Desktop/reboot-control.desktop

# Ярлык для проверки статуса обновлений
STATUS_SCRIPT="/home/ksb/check_update_status.sh"
cat > $STATUS_SCRIPT << 'EOF'
#!/bin/bash
echo "=== СТАТУС СИСТЕМЫ ОБНОВЛЕНИЙ ==="
echo ""
echo "Автоматические проверки обновлений: ❌ ОТКЛЮЧЕНЫ"
echo "Диалоговые окна обновлений: ❌ ОТКЛЮЧЕНЫ"
echo "Ручное обновление (apt update): ✅ ДОСТУПНО"
echo ""
echo "Для проверки обновлений вручную выполните:"
echo "sudo apt update"
echo ""
echo "Для установки обновлений выполните:"
echo "sudo apt upgrade"
EOF

chmod +x $STATUS_SCRIPT

echo "[Desktop Entry]
Type=Application
Exec=gnome-terminal -- bash -c '/home/ksb/check_update_status.sh; read -p \"Нажмите Enter для закрытия...\"'
Name=Статус обновлений
Comment=Проверка статуса систем обновлений
Icon=software-update-available
Terminal=false
Categories=System;" > /home/ksb/Desktop/update-status.desktop

chmod +x /home/ksb/Desktop/update-status.desktop
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME /home/ksb/Desktop/update-status.desktop

# Ярлык для переустановки дополнительного ПО
echo "[Desktop Entry]
Type=Application
Exec=gnome-terminal -- bash -c '$REINSTALL_SOFTWARE_SCRIPT'
Name=Переустановка доп. ПО
Comment=Переустановка NoMachine и Ассистент
Icon=applications-system
Terminal=false
Categories=System;" > /home/ksb/Desktop/reinstall-software.desktop

chmod +x /home/ksb/Desktop/reinstall-software.desktop
echo $PASSWORD | sudo -S chown $USERNAME:$USERNAME /home/ksb/Desktop/reinstall-software.desktop

# === ФИНАЛЬНОЕ СООБЩЕНИЕ ===

echo ""
echo "========================================="
echo "=== УСТАНОВКА ЗАВЕРШЕНА ==="
echo "========================================="
echo ""
echo "✅ Приложение установлено в: /opt/KSB_SG"
echo "✅ Служба автоперезагрузки настроена"
echo "✅ Конфигурация: /opt/KSB_SG/reboot_config.ini"
echo ""
echo "🔄 ОБНОВЛЕНИЕ КОНФИГУРАЦИИ:"
echo "   - При изменении INI файла служба автоматически перезагрузится"
echo "   - Параметр auto_reload_config = yes (включен по умолчанию)"
echo "   - Изменения применяются автоматически в течение 30-60 секунд"
echo ""
echo "🔧 Управление:"
echo "   - Ярлык на рабочем столе: 'Управление автоперезагрузкой'"
echo "   - Или выполните: sudo /opt/KSB_SG/control_reboot.sh"
echo ""
echo "📋 Другие настройки:"
echo "   - Автообновления: ОТКЛЮЧЕНЫ"
echo "   - Энергосбережение: ОТКЛЮЧЕНО"
echo "   - Закрытие крышки: ИГНОРИРУЕТСЯ"
echo "   - Раскладка клавиатуры: Русская (Alt+Shift)"
echo "   - Автозапуск приложения: ВКЛЮЧЕН"
echo ""
echo "📋 Текущие настройки автоперезагрузки:"
cat $CONFIG_INI
echo ""
echo "========================================="

# Финальное информационное окно
zenity --info \
    --title="Установка завершена" \
    --text="✅ Все настройки применены успешно!\n\n📁 Приложение: /opt/KSB_SG\n\n🔄 АВТОПЕРЕЗАГРУЗКА:\n• Конфигурация: /opt/KSB_SG/reboot_config.ini\n• Управление: ярлык на рабочем столе\n• При изменении конфига служба перезагружается автоматически\n\n📢 Система обновлений: ОТКЛЮЧЕНА\n⚡ Ручное обновление: apt update && apt upgrade\n\n🔧 Другие настройки:\n• Энергосбережение: ОТКЛЮЧЕНО\n• Закрытие крышки: ИГНОРИРУЕТСЯ\n• Раскладка: Русская (Alt+Shift)\n• Автозапуск приложения: ВКЛЮЧЕН" \
    --width=650 \
    --height=450 2>/dev/null || true