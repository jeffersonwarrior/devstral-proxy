# Changelog

All notable changes to the Devstral Proxy project will be documented in this file.

## [Unreleased]

### 🚀 Features
- Initial project structure and organization
- Core proxy functionality with OpenAI ↔ Mistral translation
- Tool call support with proper validation
- Comprehensive logging system
- Health monitoring endpoints

### 🐛 Bug Fixes
- Fixed `validate_tool_call_correspondence()` argument mismatch
- Proper handling of tool messages in message conversion
- Correct normalization of multi-part content

### 📝 Documentation
- Complete README with setup and usage instructions
- Project structure documentation
- API translation documentation

## [1.0.0] - 2024-12-12

### 🎉 Initial Release
- First stable release of Devstral Proxy
- Full OpenAI ↔ Mistral API compatibility
- Production-ready error handling
- Performance optimized for high throughput

## [0.1.0] - 2024-11-15

### 🧪 Alpha Release
- Basic proxy functionality
- Initial tool call support
- Basic error handling

---

## Contributing

Please follow the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages:

- `feat:` - A new feature
- `fix:` - A bug fix
- `docs:` - Documentation only changes
- `style:` - Changes that do not affect the meaning of the code
- `refactor:` - A code change that neither fixes a bug nor adds a feature
- `perf:` - A code change that improves performance
- `test:` - Adding missing tests or correcting existing tests
- `chore:` - Changes to the build process or auxiliary tools

## Versioning

This project adheres to [Semantic Versioning](https://semver.org/):

- **MAJOR** version when you make incompatible API changes
- **MINOR** version when you add functionality in a backwards compatible manner
- **PATCH** version when you make backwards compatible bug fixes