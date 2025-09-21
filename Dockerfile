FROM php:8.1-apache

# Instalar dependencias necesarias
RUN apt-get update && apt-get install -y \
    ghostscript \
    imagemagick \
    libreoffice \
    && rm -rf /var/lib/apt/lists/*

# Configurar directorio HOME para LibreOffice
RUN mkdir -p /home/www-data && chown www-data:www-data /home/www-data
ENV HOME /home/www-data

# Copiar archivos del proyecto
COPY . /var/www/html

# Configurar permisos
RUN chown -R www-data:www-data /var/www/html

# Habilitar mod_rewrite
RUN a2enmod rewrite

# Configurar DocumentRoot a la carpeta public
RUN echo "DocumentRoot /var/www/html/public" > /etc/apache2/sites-available/000-default.conf

# Instalar extensiones PHP necesarias
RUN docker-php-ext-install gd fileinfo

# Exponer puerto 80
EXPOSE 80

CMD ["apache2-foreground"]