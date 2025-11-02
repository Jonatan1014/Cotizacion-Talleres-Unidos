# Configuración de Proxy Inverso para API de Procesamiento de Documentos

## Problema: Error 502 Bad Gateway

El error 502 ocurre cuando el proxy (Nginx/Traefik) tiene timeouts muy cortos para procesar archivos grandes o operaciones lentas (como extraer RAR).

## Solución 1: Configuración de Nginx

Si tu servidor usa **Nginx** como proxy inverso, agrega estas configuraciones:

### Archivo: `/etc/nginx/sites-available/api-convert`

```nginx
server {
    listen 80;
    server_name convert-format.systemautomatic.xyz;

    # Límite de tamaño de archivos (debe ser >= ARCHIVE_MAX_SIZE)
    client_max_body_size 150M;
    
    # Buffer sizes para archivos grandes
    client_body_buffer_size 128k;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # TIMEOUTS CRÍTICOS - Aumentar para procesamiento de RAR
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
        send_timeout 300s;
        
        # Buffering para respuestas grandes
        proxy_buffering on;
        proxy_buffer_size 4k;
        proxy_buffers 8 4k;
        proxy_busy_buffers_size 8k;
        
        # Permitir conexiones HTTP/1.1 persistentes
        proxy_http_version 1.1;
        proxy_set_header Connection "";
    }
    
    # Configuración específica para archivos estáticos
    location /uploads/ {
        proxy_pass http://localhost:8000/uploads/;
        proxy_set_header Host $host;
        
        # Timeouts para descarga de archivos
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Aplicar cambios:

```bash
sudo nginx -t
sudo systemctl reload nginx
```

## Solución 2: Configuración de Traefik (Dokploy)

Si usas **Dokploy** (que usa Traefik), necesitas agregar labels al contenedor:

### Agregar al `docker-compose.yml`:

```yaml
services:
  api-procesamiento-documentos:
    labels:
      # Timeout de respuesta del backend (5 minutos)
      - "traefik.http.services.api-convert.loadbalancer.server.timeout=300s"
      
      # Timeout de conexión
      - "traefik.http.middlewares.api-convert-timeout.timeout.connect=300s"
      
      # Timeout de lectura de respuesta
      - "traefik.http.middlewares.api-convert-timeout.timeout.read=300s"
      
      # Timeout de escritura de request
      - "traefik.http.middlewares.api-convert-timeout.timeout.write=300s"
      
      # Aplicar middleware de timeout
      - "traefik.http.routers.api-convert.middlewares=api-convert-timeout"
```

## Solución 3: Configuración de Dokploy UI

Si usas la interfaz de Dokploy:

1. Ve a tu aplicación **API-Convert**
2. En **Settings** → **Advanced**:
   - **Request Timeout**: `300` segundos
   - **Max Request Size**: `150MB`
3. En **Environment Variables**:
   ```
   UPLOAD_MAX_SIZE=52428800
   ARCHIVE_MAX_SIZE=104857600
   CONVERSION_TIMEOUT=300
   ```

## Solución 4: Verificar Logs

### Ver logs del contenedor:

```bash
docker logs api-procesamiento-documentos --tail=100 -f
```

### Buscar errores específicos:

```bash
docker logs api-procesamiento-documentos 2>&1 | grep -i error
docker logs api-procesamiento-documentos 2>&1 | grep -i "aspose"
```

## Solución 5: Fallback - Desactivar Aspose temporalmente

Si `aspose-zip` está causando problemas (por licencia o recursos), el código ya tiene fallback a `unar`.

Para forzar uso de `unar` sin `aspose`:

### Opción A: No instalar aspose-zip

Edita `requirements.txt` y comenta:

```
# aspose-zip==23.12.0
```

### Opción B: Verificar que unar funcione

Dentro del contenedor:

```bash
docker exec -it api-procesamiento-documentos bash
which unar
unar --version
```

## Verificación Final

### 1. Verificar que el contenedor esté corriendo:

```bash
docker ps | grep api-procesamiento-documentos
```

### 2. Probar endpoint de salud:

```bash
curl https://convert-format.systemautomatic.xyz/api/health
```

### 3. Probar extracción con archivo pequeño primero:

```bash
curl -X POST https://convert-format.systemautomatic.xyz/api/uploads-ziprar \
  -F "archive=@small-test.zip" \
  -v
```

### 4. Revisar uso de recursos:

```bash
docker stats api-procesamiento-documentos
```

## Configuración Recomendada Final

### En el servidor (Dokploy/Docker):

1. **Timeout del proxy**: 300 segundos
2. **Memoria del contenedor**: 2GB
3. **CPUs**: 2 cores
4. **Tamaño máximo de request**: 150MB
5. **Workers de uvicorn**: 2

### Variables de entorno (`.env`):

```env
APP_DOMAIN=https://convert-format.systemautomatic.xyz
UPLOAD_MAX_SIZE=52428800
ARCHIVE_MAX_SIZE=104857600
CONVERSION_TIMEOUT=300
```

## Troubleshooting Común

### Error persiste después de cambios:

1. **Rebuild del contenedor**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

2. **Verificar logs en tiempo real**:
   ```bash
   docker-compose logs -f
   ```

3. **Probar directamente sin proxy**:
   ```bash
   curl -X POST http://IP_SERVIDOR:8000/api/uploads-ziprar \
     -F "archive=@test.rar"
   ```

### Si el error es específico de n8n:

En n8n, en el nodo HTTP Request:
- **Timeout**: 300000 ms (5 minutos)
- **Ignore SSL Issues**: Activar si usas SSL auto-firmado
- **Response Format**: Binary si esperas el archivo directamente

## Resumen

El error 502 generalmente es causado por:
1. ✅ **Timeouts muy cortos** → Aumentar a 300s
2. ✅ **Límite de tamaño pequeño** → Aumentar a 150MB
3. ✅ **Memoria insuficiente** → Asignar 2GB
4. ⚠️ **Aspose-zip con problemas** → Usar fallback `unar`
