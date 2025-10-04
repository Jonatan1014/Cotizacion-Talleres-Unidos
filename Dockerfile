FROM php:8.1-apache

# Install system dependencies including xvfb for headless LibreOffice
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
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg
RUN docker-php-ext-install -j$(nproc) gd zip pdo_mysql

# Enable Apache modules
RUN a2enmod rewrite


# Copy custom PHP configuration
COPY ./app/php.ini /usr/local/etc/php/conf.d/custom.ini
# Configure Apache to serve files from /var/www/html
COPY ./app /var/www/html

# Create directories with proper permissions
RUN mkdir -p /tmp/libreoffice /var/www/.config/libreoffice
RUN chown -R www-data:www-data /var/www/html /tmp/libreoffice
RUN chmod -R 777 /tmp

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]