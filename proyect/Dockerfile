FROM php:8.1-apache

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    libzip-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    ghostscript \
    libreoffice \
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar extensiones de PHP
RUN docker-php-ext-install \
    zip \
    gd \
    exif \
    mysqli \
    pdo_mysql

# Configurar Apache
RUN a2enmod rewrite

# Crear directorios necesarios
RUN mkdir -p /var/www/html/uploads /var/www/html/logs

# Copiar archivos de la aplicación (CORREGIDO)
COPY ./app/ /var/www/html/

# Establecer permisos
RUN chown -R www-data:www-data /var/www/html/
RUN chmod -R 755 /var/www/html/uploads/
RUN chmod -R 755 /var/www/html/logs/

# Instalar Composer y dependencias
WORKDIR /var/www/html
RUN curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN if [ -f composer.json ]; then composer install --no-dev --optimize-autoloader; else echo "No composer.json file found"; fi

EXPOSE 80