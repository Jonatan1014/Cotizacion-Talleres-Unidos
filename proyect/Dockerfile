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
    imagemagick \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Instalar extensiones de PHP
RUN docker-php-ext-install \
    zip \
    gd \
    exif \
    mysqli \
    pdo_mysql

# Instalar Composer
COPY --from=composer:latest /usr/bin/composer /usr/bin/composer

# Configurar Apache
RUN a2enmod rewrite
COPY ./apache-config.conf /etc/apache2/sites-available/000-default.conf

# Crear directorios necesarios
RUN mkdir -p /var/www/html/uploads /var/www/html/logs

# Copiar archivos de la aplicación
COPY ./app /var/www/html/

# Establecer permisos
RUN chown -R www-data:www-data /var/www/html/
RUN chmod -R 755 /var/www/html/uploads/
RUN chmod -R 755 /var/www/html/logs/

# Instalar dependencias de PHP
WORKDIR /var/www/html
RUN composer require \
    phpoffice/phpword \
    phpoffice/phpspreadsheet \
    guzzlehttp/guzzle \
    setasign/fpdi

EXPOSE 80