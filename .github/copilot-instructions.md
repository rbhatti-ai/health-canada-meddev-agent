# Copilot Instructions for Health Canada Medical Device Regulatory Compliance Agent

## Project Overview

This is an AI-powered Health Canada medical device regulatory compliance assistant. The project helps manufacturers understand:
- Device classification
- Regulatory pathways
- Documentation requirements
- Compliance timelines

## Domain Context

### Health Canada Regulatory Framework
- Familiarize yourself with Health Canada's Medical Devices Regulations (MDR)
- Understand device risk classifications (Class I, II, III, IV)
- Be aware of regulatory pathways: Medical Device License (MDL), Medical Device Establishment License (MDEL)
- Consider Quality Management System (QMS) requirements (ISO 13485)

### Key Terminology
- **MDEL**: Medical Device Establishment License
- **MDL**: Medical Device License
- **QMS**: Quality Management System
- **ISO 13485**: International standard for medical device quality management
- **Risk classification**: Categorization based on potential risk to users (Class I-IV)

## Coding Standards

### General Principles
- Write clear, maintainable code with regulatory compliance in mind
- Prioritize accuracy and reliability over performance
- Include comprehensive error handling and validation
- Document all regulatory-related business logic thoroughly

### Code Style
- Use descriptive variable and function names that reflect regulatory terminology
- Follow industry-standard naming conventions for the chosen programming language
- Keep functions focused and single-purpose
- Add comments for complex regulatory logic or calculations

### Documentation
- All functions dealing with regulatory logic must have clear docstrings
- Include references to relevant Health Canada regulations or guidance documents
- Document assumptions about regulatory requirements
- Maintain a clear changelog for regulatory logic updates

## Testing Requirements

### Test Coverage
- Write comprehensive unit tests for all regulatory logic
- Include edge cases and boundary conditions
- Test validation logic thoroughly
- Verify correct device classification outputs

### Test Data
- Use realistic medical device scenarios in test cases
- Include examples from all device risk classes
- Test with both valid and invalid regulatory data
- Ensure compliance data is anonymized if using real examples

## Security and Compliance

### Data Handling
- Never hardcode sensitive information (API keys, credentials)
- Ensure all regulatory data is handled securely
- Follow privacy best practices for any manufacturer information
- Validate all user inputs to prevent security vulnerabilities

### Regulatory Accuracy
- Cross-reference regulatory guidance with official Health Canada sources
- Clearly mark any information that may require verification
- Include disclaimers where appropriate
- Keep regulatory information up-to-date

## AI Agent Development

### Natural Language Processing
- Ensure accurate interpretation of regulatory questions
- Provide clear, structured responses
- Include confidence indicators where appropriate
- Offer sources and references for regulatory guidance

### User Experience
- Responses should be clear and actionable
- Use plain language while maintaining regulatory accuracy
- Provide step-by-step guidance for complex processes
- Include examples and templates where helpful

## Dependencies and Libraries

### Version Management
- Keep dependencies up-to-date, especially security-related packages
- Document the purpose of each major dependency
- Consider stability and maintenance of chosen libraries

### AI/ML Libraries
- Use well-established libraries for NLP and AI functionality
- Document model versions and training data sources
- Ensure reproducibility of AI behaviors

## Error Handling

### User-Facing Errors
- Provide helpful error messages with suggested solutions
- Include relevant regulatory context in error messages
- Log errors appropriately for debugging

### Validation
- Validate all regulatory data inputs
- Check for completeness of required information
- Provide clear feedback on validation failures

## Performance Considerations

- Balance response time with accuracy for regulatory queries
- Optimize database queries for regulatory information retrieval
- Cache frequently accessed regulatory data appropriately
- Monitor resource usage for AI model inference

## Contributing Guidelines

### Code Reviews
- Verify regulatory accuracy in code reviews
- Check for proper error handling
- Ensure adequate test coverage
- Review documentation completeness

### Commit Messages
- Use clear, descriptive commit messages
- Reference issue numbers when applicable
- Note any regulatory logic changes explicitly

## Resources

- [Health Canada Medical Devices](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices.html)
- [Medical Devices Regulations (SOR/98-282)](https://laws-lois.justice.gc.ca/eng/regulations/SOR-98-282/)
- [ISO 13485 Standard](https://www.iso.org/standard/59752.html)
- [Guidance Documents for Medical Devices](https://www.canada.ca/en/health-canada/services/drugs-health-products/medical-devices/application-information/guidance-documents.html)

## Notes for Copilot

- Prioritize regulatory accuracy and compliance in all suggestions
- When uncertain about regulatory requirements, indicate the need for verification
- Suggest appropriate disclaimers for regulatory advice
- Consider both manufacturer and Health Canada perspectives
- Stay current with regulatory updates and changes
