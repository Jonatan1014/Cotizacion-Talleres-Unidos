# Dockerfile
FROM php:8.1-apache

# Install system dependencies including xvfb for headless LibreOffice
# Cambiamos unrar y rar por p7zip-full que incluye 7z, útil para varios formatos
RUN apt-get update && apt-get install -y \
    libzip-dev \
    libpng-dev \
    libjpeg-dev \
    libfreetype6-dev \
    ghostscript \
    libreoffice \
    libreoffice-core \
    libreoffice-common \
    libreoffice-writer \
    libreoffice-calc \
    poppler-utils \
    xvfb \
    unzip \
    p7zip-full \ 
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg
RUN docker-php-ext-install -j$(nproc) gd zip pdo_mysql

# Enable Apache modules
RUN a2enmod rewrite

# Copy custom PHP configuration
COPY ./app/php.ini /usr/local/etc/php/conf.d/custom.ini

# Copy application files
COPY . /var/www/html/

# Install Composer dependencies
RUN cd /var/www/html && curl -sS https://getcomposer.org/installer | php -- --install-dir=/usr/local/bin --filename=composer
RUN cd /var/www/html && composer install --no-dev --optimize-autoloader

# Create directories with proper permissions
RUN mkdir -p /tmp/libreoffice /var/www/.config/libreoffice
RUN chown -R www-data:www-data /var/www/html /tmp/libreoffice
RUN chmod -R 777 /tmp

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]