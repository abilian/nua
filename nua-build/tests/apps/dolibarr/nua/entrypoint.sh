#!/bin/bash -eux

# version_greater A B returns whether A > B
function version_greater() {
	[[ "$(printf '%s\n' "$@" | sort -nt. | head -n 1)" != "$1" ]];
}

# return true if specified directory is empty
function directory_empty() {
	[ "$(find "$1"/ -mindepth 1 -maxdepth 1 | wc -l)" = "0" ]
}

function run_as() {
	if [[ $EUID -eq 0 ]]; then
		su - apache -s /bin/bash -c "$1"
	else
		bash -c "$1"
	fi
}


if [ ! -d /var/www/documents ]; then
	mkdir -p /var/www/documents
fi
chown -R apache:root /var/www/documents
chmod -R ug+w /var/www/documents

if [ ! -d /var/www/html/conf ]; then
	mkdir -p /var/www/html/conf
fi
chown apache:root /var/www/html/conf
chmod 550 /var/www/html/conf

chown apache:root /run/apache2
chmod 770 /run/apache2

# Create a default config
if [ ! -f /var/www/html/conf/conf.php ]; then
	cat <<-EOF > /var/www/html/conf/conf.php
		<?php
		// Config file for Dolibarr ${DOLI_VERSION} ($(date))

		// ###################
		// # Main parameters #
		// ###################
		\$dolibarr_main_url_root='${DOLI_URL_ROOT}';
		\$dolibarr_main_document_root='/var/www/html';
		\$dolibarr_main_url_root_alt='/custom';
		\$dolibarr_main_document_root_alt='/var/www/html/custom';
		\$dolibarr_main_data_root='/var/www/documents';
		\$dolibarr_main_db_host='${DOLI_DB_HOST}';
		\$dolibarr_main_db_port='${DOLI_DB_PORT}';
		\$dolibarr_main_db_name='${DOLI_DB_NAME}';
		\$dolibarr_main_db_prefix='${DOLI_DB_PREFIX}';
		\$dolibarr_main_db_user='${DOLI_DB_USER}';
		\$dolibarr_main_db_pass='${DOLI_DB_PASSWORD}';
		\$dolibarr_main_db_type='${DOLI_DB_TYPE}';
		\$dolibarr_main_db_character_set='${DOLI_DB_CHARACTER_SET}';
		\$dolibarr_main_db_collation='${DOLI_DB_COLLATION}';

		// ##################
		// # Login          #
		// ##################
		\$dolibarr_main_authentication='${DOLI_AUTH}';
		\$dolibarr_main_auth_ldap_host='${DOLI_LDAP_HOST}';
		\$dolibarr_main_auth_ldap_port='${DOLI_LDAP_PORT}';
		\$dolibarr_main_auth_ldap_version='${DOLI_LDAP_VERSION}';
		\$dolibarr_main_auth_ldap_servertype='${DOLI_LDAP_SERVERTYPE}';
		\$dolibarr_main_auth_ldap_login_attribute='${DOLI_LDAP_LOGIN_ATTRIBUTE}';
		\$dolibarr_main_auth_ldap_dn='${DOLI_LDAP_DN}';
		\$dolibarr_main_auth_ldap_filter ='${DOLI_LDAP_FILTER}';
		\$dolibarr_main_auth_ldap_admin_login='${DOLI_LDAP_ADMIN_LOGIN}';
		\$dolibarr_main_auth_ldap_admin_pass='${DOLI_LDAP_ADMIN_PASS}';
		\$dolibarr_main_auth_ldap_debug='${DOLI_LDAP_DEBUG}';

		// ##################
		// # Security       #
		// ##################
		\$dolibarr_main_prod='${DOLI_PROD}';
		\$dolibarr_main_force_https='${DOLI_HTTPS}';
		\$dolibarr_main_restrict_os_commands='mysqldump, mysql, pg_dump, pgrestore';
		\$dolibarr_nocsrfcheck='${DOLI_NO_CSRF_CHECK}';
		\$dolibarr_main_cookie_cryptkey='$(openssl rand -hex 32)';
		\$dolibarr_mailing_limit_sendbyweb='0';
		EOF
fi
chown apache:root /var/www/html/conf/conf.php
chmod 440 /var/www/html/conf/conf.php

# Detect installed version (docker specific solution)
installed_version="0.0.0~unknown"
if [ -f /var/www/documents/install.version ]; then
	installed_version=$(cat /var/www/documents/install.version)
fi
image_version=${DOLI_VERSION}

if version_greater "$installed_version" "$image_version"; then
	echo "Can't start Dolibarr because the version of the data ($installed_version) is higher than the docker image version ($image_version) and downgrading is not supported. Are you sure you have pulled the newest image version?"
	exit 1
fi

# Initialize image
if version_greater "$image_version" "$installed_version"; then
	echo "Dolibarr initialization..."
	rsync_options="--verbose --archive --chmod a-w --chown apache:root"

	rsync $rsync_options --delete --exclude /conf/ --exclude /custom/ --exclude /theme/ /nua/build/dolibarr/htdocs/ /var/www/html/

	for dir in conf custom; do
		if [ ! -d /var/www/html/"$dir" ] || directory_empty /var/www/html/"$dir"; then
			rsync $rsync_options --include /"$dir"/ --exclude '/*' /nua/build/dolibarr/htdocs/ /var/www/html/
		fi
	done

	# The theme folder contains custom and official themes. We must copy even if folder is not empty, but not delete existing content
	for dir in theme; do
		rsync $rsync_options --include /"$dir"/ --exclude '/*' /nua/build/dolibarr/htdocs/ /var/www/html/
	done

	if [ "$installed_version" != "0.0.0~unknown" ]; then

		# Call upgrade scripts if needed
		# https://wiki.dolibarr.org/index.php/Installation_-_Upgrade#With_Dolibarr_.28standard_.zip_package.29
		echo "Dolibarr upgrade from $installed_version to $image_version..."

		if [ -f /var/www/documents/install.lock ]; then
			rm /var/www/documents/install.lock
		fi

		base_version=(${installed_version//./ })
		target_version=(${image_version//./ })

		# Call upgrade scripts
		chmod 660 /var/www/html/conf/conf.php
		run_as "cd /var/www/html/install/ && php upgrade.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
		run_as "cd /var/www/html/install/ && php upgrade2.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
		run_as "cd /var/www/html/install/ && php step5.php ${base_version[0]}.${base_version[1]}.0 ${target_version[0]}.${target_version[1]}.0"
		chmod 440 /var/www/html/conf/conf.php

	elif [ ! -f /var/www/documents/install.lock ]; then

		# Create forced values for first install
		cat <<-EOF > /var/www/html/install/install.forced.php
			<?php
			// Forced install config file for Dolibarr ${DOLI_VERSION} ($(date))
			\$force_install_nophpinfo = true;
			\$force_install_noedit = 2;
			\$force_install_message = 'Dolibarr installation';
			\$force_install_main_data_root = '/var/www/documents';
			\$force_install_mainforcehttps = !empty('${DOLI_HTTPS}');
			\$force_install_database = '${DOLI_DB_NAME}';
			\$force_install_type = '${DOLI_DB_TYPE}';
			\$force_install_dbserver = '${DOLI_DB_HOST}';
			\$force_install_port = '${DOLI_DB_PORT}';
			\$force_install_prefix = '${DOLI_DB_PREFIX}';
			\$force_install_databaselogin = '${DOLI_DB_USER}';
			\$force_install_databasepass = '${DOLI_DB_PASSWORD}';
			\$force_install_createuser = !empty('${DOLI_DB_ROOT_LOGIN}');
			\$force_install_createdatabase = !empty('${DOLI_DB_ROOT_LOGIN}');
			\$force_install_databaserootlogin = '${DOLI_DB_ROOT_LOGIN}';
			\$force_install_databaserootpass = '${DOLI_DB_ROOT_PASSWORD}';
			\$force_install_dolibarrlogin = '${DOLI_ADMIN_LOGIN}';
			\$force_install_lockinstall = true;
			\$force_install_module = '${DOLI_MODULES}';
			EOF

		# Call install scripts
		chmod 660 /var/www/html/conf/conf.php
		run_as "cd /var/www/html/install/ && php step2.php set"
		run_as "cd /var/www/html/install/ && php step5.php 0 0 ${LANG:-fr_FR} set ${DOLI_ADMIN_LOGIN} ${DOLI_ADMIN_PASSWORD} ${DOLI_ADMIN_PASSWORD}"
		chmod 440 /var/www/html/conf/conf.php

	fi

	echo 'This is a lock file to prevent use of install pages (generated by container entrypoint)' > /var/www/documents/install.lock
	chown apache:apache /var/www/documents/install.lock
	chmod 440 /var/www/documents/install.lock
fi

chown apache:root /var/www/html/custom
chmod 775 /var/www/html/custom

if [ -f /var/www/documents/install.lock ]; then
	echo $image_version > /var/www/documents/install.version
fi
