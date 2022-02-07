## ----------------------------------------------------------------------
## Makefile for blockchain-sim.dataekspeditioner.dk
##
## Used for both development and production. See targets below.
## ----------------------------------------------------------------------

help:   # Show this help.
	@sed -ne '/@sed/!s/## //p' $(MAKEFILE_LIST)

# ---------- Development ---------- #
build:  ## Build or rebuild development docker image
	docker-compose -f docker-compose.dev.yml build

develop:  ## Run development server
	docker-compose -f docker-compose.dev.yml up --remove-orphans

stop: ## Stop developmentment server
	docker-compose -f docker-compose.dev.yml down --remove-orphans

shell:  ## Open shell in running docker development container
	docker-compose -f docker-compose.dev.yml exec web /bin/bash

migrations: # make migrations
	docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

migrate: # make migrations
	docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

dev_superuser: # make development superuser 
	docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser


# ---------- Checks and tests ---------- #
test: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run --rm web pytest

test_models: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_models.py

test_forms: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_forms.py

test_views: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_views.py


# ---------- Codestyle  ---------- #
tidy_bcsim: # Reformat source code to make it adhere to PEP8
	docker-compose -f docker-compose.dev.yml exec web autopep8 --in-place --recursive --exclude=migrations,animal_avatar bcsim

check_views: # Check PEP8 standards for views.py file
	docker-compose -f docker-compose.dev.yml exec web pycodestyle bcsim/views.py

check_views_show_source: #jierj
	docker-compose -f docker-compose.dev.yml exec web pycodestyle --show-source --show-pep8 bcsim/views.py

# ---------- Production ---------- #
production_stop: ## Stop production server
	docker-compose -f docker-compose.prod.yml down --remove-orphans

production_start: ## Start production server as daemon
	docker-compose -f docker-compose.prod.yml up --build --remove-orphans -d

production_djangologs: ## Show django logs
	docker logs blockchainsimdataekspeditionerdk_web_1

production_accesslogs: ## Show nginx access logs
	docker logs blockchainsimdataekspeditionerdk_nginx_1

production_shell: # Open shell in running docker production container
	docker-compose -f docker-compose.prod.yml exec web /bin/bash

