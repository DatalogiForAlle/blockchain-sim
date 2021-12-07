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

# ---------- Checks and tests ---------- #
test: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run --rm web pytest

test_models: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_models.py

test_forms: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_forms.py

test_views: ## Execute tests within the docker image
	DJANGO_SETTINGS_MODULE=config.settings docker-compose -f docker-compose.dev.yml run web pytest bcsim/tests/test_views.py


flake8: ## PEP8 codestyle check
	flake8 --exclude bcsim/migrations --extend-exclude accounts/migrations

# This target runs both PEP8 checks and test suite
check: flake8 test

tidy:   ## Reformat source files to adhere to PEP8 
	black -79 . --exclude=bcsim/migrations --extend-exclude=accounts/migrations


migrations: # make migrations
	docker-compose -f docker-compose.dev.yml exec web python manage.py makemigrations

migrate: # make migrations
	docker-compose -f docker-compose.dev.yml exec web python manage.py migrate

dev_superuser: # make development superuser 
	docker-compose -f docker-compose.dev.yml exec web python manage.py createsuperuser



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

