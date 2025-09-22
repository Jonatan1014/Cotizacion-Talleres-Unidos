FROM php:8.1-apache

# Install system dependencies
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
    poppler-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install PHP extensions
RUN docker-php-ext-configure gd --with-freetype --with-jpeg
RUN docker-php-ext-install -j$(nproc) gd zip pdo_mysql

# Enable Apache modules
RUN a2enmod rewrite

# Configure Apache to serve files from /var/www/html
COPY ./app /var/www/html

# Create user directory for LibreOffice
RUN mkdir -p /var/www/.config/libreoffice
RUN chown -R www-data:www-data /var/www/.config

# Set permissions
RUN chown -R www-data:www-data /var/www/html
RUN chmod -R 755 /var/www/html

# Expose port
EXPOSE 80

# Start Apache
CMD ["apache2-foreground"]