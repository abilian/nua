<?php
// Config file install.forced.php {{DOLI_VERSION}}}}
// Date: {{DATE}}

// Main parameters
$dolibarr_main_url_root='{{DOLI_URL_ROOT}}';
$dolibarr_main_document_root='/var/www/html';
$dolibarr_main_url_root_alt='/custom';
$dolibarr_main_document_root_alt='/var/www/html/custom';
$dolibarr_main_data_root='/var/www/documents';
$dolibarr_main_db_host='{{DOLI_DB_HOST}}';
$dolibarr_main_db_port='{{DOLI_DB_PORT}}';
$dolibarr_main_db_name='{{DOLI_DB_NAME}}';
$dolibarr_main_db_prefix='{{DOLI_DB_PREFIX}}';
$dolibarr_main_db_user='{{DOLI_DB_USER}}';
$dolibarr_main_db_pass='{{DOLI_DB_PASSWORD}}';
$dolibarr_main_db_type='{{DOLI_DB_TYPE}}';
$dolibarr_main_db_character_set='utf8';
$dolibarr_main_db_collation='utf8_unicode_ci';

// Login
$dolibarr_main_authentication='{{DOLI_AUTH}}';
$dolibarr_main_auth_ldap_host='{{DOLI_LDAP_HOST}}';
$dolibarr_main_auth_ldap_port='{{DOLI_LDAP_PORT}}';
$dolibarr_main_auth_ldap_version='{{DOLI_LDAP_VERSION}}';
$dolibarr_main_auth_ldap_servertype='{{DOLI_LDAP_SERVERTYPE}}';
$dolibarr_main_auth_ldap_login_attribute='{{DOLI_LDAP_LOGIN_ATTRIBUTE}}';
$dolibarr_main_auth_ldap_dn='{{DOLI_LDAP_DN}}';
$dolibarr_main_auth_ldap_filter ='{{DOLI_LDAP_FILTER}}';
$dolibarr_main_auth_ldap_admin_login='{{DOLI_LDAP_ADMIN_LOGIN}}';
$dolibarr_main_auth_ldap_admin_pass='{{DOLI_LDAP_ADMIN_PASS}}';
$dolibarr_main_auth_ldap_debug='{{DOLI_LDAP_DEBUG}}';

//  Security
$dolibarr_main_prod='{{DOLI_PROD}}';
$dolibarr_main_force_https='{{DOLI_FORCE_HTTPS}}';
$dolibarr_main_restrict_os_commands='mysqldump, mysql, pg_dump, pgrestore';
$dolibarr_nocsrfcheck='{{DOLI_NO_CSRF_CHECK}}';
$dolibarr_main_cookie_cryptkey='{{CRYPTKEY}}';
$dolibarr_mailing_limit_sendbyweb='0';
