FROM php:8.1-apache

# Instalar dependencias del sistema necesarias para conversión y GD
RUN apt-get update && apt-get install -y \
    ghostscript \
    imagemagick \
    libreoffice \
    libfreetype6-dev \
    libjpeg62-turbo-dev \
    libpng-dev \
    zlib1g-dev \
    libzip-dev \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio HOME para LibreOffice
RUN mkdir -p /home/www-data && chown www-data:www-data /home/www-data
ENV HOME /home/www-data

# Instalar extensiones PHP necesarias (GD y fileinfo con sus dependencias)
RUN docker-php-ext-configure gd --with-freetype --with-jpeg \
    && docker-php-ext-install -j$(nproc) gd fileinfo zip

# Copiar archivos del proyecto
COPY . /var/www/html

# Configurar permisos
RUN chown -R www-data:www-data /var/www/html

# Habilitar mod_rewrite
RUN a2enmod rewrite

# ✅ AÑADIDO: Evitar advertencia de Apache
RUN echo "ServerName localhost" >> /etc/apache2/apache2.conf

# Configurar DocumentRoot a la carpeta public
RUN echo "DocumentRoot /var/www/html/public" > /etc/apache2/sites-available/000-default.conf

# Exponer puerto 80
EXPOSE 80

CMD ["apache2-foreground"]