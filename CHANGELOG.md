# Changelog

## [0.1.2](https://github.com/vdella/weather-ingest-api/compare/v0.1.1...v0.1.2) (2026-11-22)


### Documentation

* **adr:** stop pointing at the removed future-work list ([cd00693](https://github.com/vdella/weather-ingest-api/commit/cd0069338290be926abca7924610ada0a3abeac0))
* remove the "What I Would Do With More Time" section from the README ([dc30c66](https://github.com/vdella/weather-ingest-api/commit/dc30c66b9bbc2092d941bcfa25b13b9c44cd4ddd))

## [0.1.1](https://github.com/vdella/weather-ingest-api/compare/v0.1.0...v0.1.1) (2026-11-22)


### Bug Fixes

* **release:** tag releases as vX.Y.Z and tag images from release outputs ([8ba5ca2](https://github.com/vdella/weather-ingest-api/commit/8ba5ca2d145b3c2d3c1fc6686a4e1140291e17ae))

## 0.1.0 (2026-11-22)


### Features

* **api:** add /health with a database connectivity check ([e38a7df](https://github.com/vdella/weather-ingest-api/commit/e38a7df3afc6d811bdc94221bd018239b0658f3e))
* **api:** add REST response schemas ([21ee59f](https://github.com/vdella/weather-ingest-api/commit/21ee59f6eb91716e409bc0d073b854ee591114ec))
* **api:** expose weather readings through a versioned REST API ([5618498](https://github.com/vdella/weather-ingest-api/commit/5618498b8d718209970bc2346a193342e91fa1d7))
* **config:** load typed settings from the environment ([553617b](https://github.com/vdella/weather-ingest-api/commit/553617bf2c98be919f6d4cc21f24bcd0c18028e9))
* **extraction:** add OpenWeather current weather client ([8e2c257](https://github.com/vdella/weather-ingest-api/commit/8e2c257647309938388b3df6df8aedca991b5d38))
* **extraction:** add weather-ingest CLI to fetch a city on demand ([d998130](https://github.com/vdella/weather-ingest-api/commit/d998130105da1533d7a4098d40bfd858c8af1b0e))
* **extraction:** model the OpenWeather current weather payload ([4df0650](https://github.com/vdella/weather-ingest-api/commit/4df06503cf6b61623e5d4690c6abda5329b69f08))
* **storage:** add `weather-ingest ingest` to fetch and store a city ([91d11f2](https://github.com/vdella/weather-ingest-api/commit/91d11f2569838835af2bdefecbba2105bb8d247c))
* **storage:** add Alembic and the initial weather_readings migration ([13f92f7](https://github.com/vdella/weather-ingest-api/commit/13f92f755be2397af7d89aadfb97183146cdd2fa))
* **storage:** add case- and accent-insensitive city lookup keys ([d25772f](https://github.com/vdella/weather-ingest-api/commit/d25772f92079186ac1a6f4957f5a2b49871e6e2c))
* **storage:** add the ingestion service (fetch, map, upsert) ([3947593](https://github.com/vdella/weather-ingest-api/commit/394759371fe3e74d8602de5a029a38d4c94266b8))
* **storage:** add the weather_readings ORM model ([af669d4](https://github.com/vdella/weather-ingest-api/commit/af669d4f4d4a4f055e92cd39e4ebbee3e83b1c19))
* **storage:** add WeatherReadingRepository with idempotent upsert ([6b2d1f0](https://github.com/vdella/weather-ingest-api/commit/6b2d1f027c1fa7b7544120aabcce46327ea2f927))
* **storage:** configure the database engine and session factory ([5555d52](https://github.com/vdella/weather-ingest-api/commit/5555d527e597ffb1d1b709fcfffe03860d1a1b73))


### Bug Fixes

* **release:** bump the project version in uv.lock with each release ([50b7a76](https://github.com/vdella/weather-ingest-api/commit/50b7a76ee9f62ce4f01318eba251531db142ef92))


### Documentation

* add project README ([bd0e759](https://github.com/vdella/weather-ingest-api/commit/bd0e7594aac12fb3cd375f85764b93c67f729aa3))
* **adr:** add ADR process, template and toolchain decision ([05d07dc](https://github.com/vdella/weather-ingest-api/commit/05d07dc959e4be2e3580957f834cc8de17cef6c5))
* **adr:** record the database stack and table design (ADR-0005, ADR-0006) ([9057324](https://github.com/vdella/weather-ingest-api/commit/90573246b5b4d47d4f84624eee331bfb4f187872))
* **adr:** record the Docker and Compose design (ADR-0008) ([f8f5a66](https://github.com/vdella/weather-ingest-api/commit/f8f5a66caf150f89d3146a7c5029d392df7af153))
* **adr:** record the OpenWeather client design (ADR-0004) ([d49a4be](https://github.com/vdella/weather-ingest-api/commit/d49a4be1381716df8c9bdb783422ce4571841d80))
* **adr:** record the REST API design (ADR-0007) ([af42427](https://github.com/vdella/weather-ingest-api/commit/af424270355c990f610e2a2c87858ce4756e70fe))
* **api:** add a Postman collection ([182b830](https://github.com/vdella/weather-ingest-api/commit/182b830a1231a062506959d90cb43f5255535251))
* describe the weather_readings table and the ingest command ([5b0b67a](https://github.com/vdella/weather-ingest-api/commit/5b0b67ae0efe348b27c94e1136f7badc02daaa20))
* document running and operating the stack with Docker Compose ([f9d0f90](https://github.com/vdella/weather-ingest-api/commit/f9d0f901213a3110115579adae36ef128c0c0ffc))
* document the REST API, its errors and the Postman collection ([e6cd93a](https://github.com/vdella/weather-ingest-api/commit/e6cd93a6571a71bb842ef9ecc3e4ab7de4f679ee))
* document the weather-ingest fetch command ([a2f989b](https://github.com/vdella/weather-ingest-api/commit/a2f989b1bb2c7bd06ab32af14b9305ea70bcd64a))
