<?php
// Forced install config file for Dolibarr {{DOLI_VERSION}}
// Date: {{DATE}}

$force_install_nophpinfo = true;
$force_install_noedit = 2;
$force_install_message = 'Dolibarr installation';
$force_install_main_data_root = '/var/www/documents';
$force_install_mainforcehttps = !empty('{{DOLI_FORCE_HTTPS}}');
$force_install_database = '{{DOLI_DB_NAME}}';
$force_install_type = '{{DOLI_DB_TYPE}}';
$force_install_dbserver = '{{DOLI_DB_HOST}}';
$force_install_port = '{{DOLI_DB_PORT}}';
$force_install_prefix = '{{DOLI_DB_PREFIX}}';
$force_install_databaselogin = '{{DOLI_DB_USER}}';
$force_install_databasepass = '{{DOLI_DB_PASSWORD}}';
$force_install_createuser = !empty('{{DOLI_DB_ROOT_LOGIN}}');
$force_install_createdatabase = !empty('{{DOLI_DB_ROOT_LOGIN}}');
$force_install_databaserootlogin = '{{DOLI_DB_ROOT_LOGIN}}';
$force_install_databaserootpass = '{{DOLI_DB_ROOT_PASSWORD}}';
$force_install_dolibarrlogin = '{{DOLI_ADMIN_LOGIN}}';
$force_install_lockinstall = true;
$force_install_module = '{{DOLI_MODULES}}';
