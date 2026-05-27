FROM nginxinc/nginx-unprivileged:alpine

USER root

RUN rm -rf /usr/share/nginx/html/*

USER nginx

COPY index.html /usr/share/nginx/html/index.html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]