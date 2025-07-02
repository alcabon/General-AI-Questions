Salesforce Apex and LWC Best Practices Guide
This guide provides essential best practices for developing secure, performant, and maintainable Salesforce applications using Apex and Lightning Web Components (LWC). Based on industry standards, Salesforce Winter '25 (September 2024) updates, and CodeScan rules (version 25.1.3), it is designed for developers and AI-driven code analysis.
Apex Best Practices
1. Prevent SOQL Injection

Description: Dynamic SOQL queries with unescaped user input can lead to SOQL injection vulnerabilities, allowing unauthorized data access.
Non-compliant Example:String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
Database.query(query);


Compliant Example:String query = 'SELECT Id FROM Account WHERE Name = :userInput';
Database.query(query);


Recommendation: Use bind variables (:variable) or String.escapeSingleQuotes() to sanitize user input.

2. Avoid DML Operations in Loops

Description: Performing DML operations (e.g., insert, update) inside loops can exceed Salesforce governor limits, causing runtime errors.
Non-compliant Example:for (Account acc : accounts) {
    update acc;
}


Compliant Example:List<Account> toUpdate = new List<Account>();
for (Account acc : accounts) {
    toUpdate.add(acc);
}
update toUpdate;


Recommendation: Collect records in a list and perform DML operations outside loops.

3. Avoid Hardcoding IDs

Description: Hardcoding record IDs makes code non-portable across orgs and environments, leading to deployment issues.
Non-compliant Example:Account acc = [SELECT Id FROM Account WHERE Id = '001xxxxxxxxxxxx'];


Compliant Example:Account acc = [SELECT Id FROM Account WHERE Name = 'Test Account'];


Recommendation: Use queries, custom metadata, or custom settings to reference records dynamically.

4. Ensure Unit Tests Include Assertions

Description: Unit tests without assertions fail to validate expected behavior, reducing test reliability.
Non-compliant Example:@IsTest
void testMethod() {
    Account acc = new Account(Name = 'Test');
    insert acc;
}


Compliant Example:@IsTest
void testMethod() {
    Account acc = new Account(Name = 'Test');
    insert acc;
    System.assertEquals('Test', [SELECT Name FROM Account].Name, 'Account name should match');
}


Recommendation: Use System.assert, System.assertEquals, or System.assertNotEquals in all test methods.

5. Limit Class and Method Complexity

Description: Overly complex classes or methods (e.g., high cognitive complexity or excessive lines) are hard to maintain and prone to errors.
Non-compliant Example:public class LargeClass {
    // 2000 lines with nested loops and conditions
    public void complexMethod() { ... }
}


Compliant Example:public class AccountService {
    // Smaller, focused class
    public void updateAccounts(List<Account> accounts) { ... }
}


Recommendation: Keep classes under 1000 lines and methods under 100 lines; refactor complex logic into smaller methods.

6. Avoid Global Modifier Unless Necessary

Description: Using global locks classes/methods in managed packages, limiting future modifications.
Non-compliant Example:global class JobSyncScheduler implements Schedulable {
    global void execute(SchedulableContext ctx) {}
}


Compliant Example:public class JobSyncScheduler implements Schedulable {
    public void execute(SchedulableContext ctx) {}
}


Recommendation: Use public or private unless global is required for external APIs.

7. Prevent XSS in Apex Output

Description: Outputting unescaped data in Visualforce (e.g., with escape=false) can lead to cross-site scripting (XSS) vulnerabilities.
Non-compliant Example:public String getContent() {
    return '<script>maliciousCode()</script>';
}


Compliant Example:public String getContent() {
    return String.escapeHtml4('<script>maliciousCode()</script>');
}


Recommendation: Use String.escapeHtml4() or ensure escape=true in Visualforce bindings.

8. Avoid Excessive SOQL Queries

Description: Multiple SOQL queries in a transaction can hit governor limits (100 queries per transaction).
Non-compliant Example:for (Id accId : accountIds) {
    Account acc = [SELECT Name FROM Account WHERE Id = :accId];
}


Compliant Example:Map<Id, Account> accounts = new Map<Id, Account>([SELECT Id, Name FROM Account WHERE Id IN :accountIds]);


Recommendation: Use bulk SOQL queries and store results in maps or lists.

Lightning Web Components (LWC) Best Practices
9. Use HTTPS for External Requests

Description: Making HTTP requests instead of HTTPS risks data interception in LWC.
Non-compliant Example:fetch('http://example.com/data')
    .then(response => response.json());


Compliant Example:fetch('https://example.com/data')
    .then(response => response.json());


Recommendation: Always use HTTPS for external API calls.

10. Avoid Inline JavaScript in LWC

Description: Inline JavaScript in LWC templates increases the risk of XSS vulnerabilities.
Non-compliant Example:<template>
    <div onclick={handleClick}>Click me</div>
</template>


Compliant Example:<template>
    <div onclick={handleClick}>Click me</div>
</template>
<script>
export default class MyComponent extends LightningElement {
    handleClick() {
        // Handle logic in JavaScript
    }
}
</script>


Recommendation: Define event handlers in the JavaScript file, not in the template.

11. Follow TypeScript Conventions (Winter '25)

Description: LWC supports TypeScript in Winter '25, requiring proper type annotations for maintainability.
Non-compliant Example:export default class MyComponent extends LightningElement {
    myVar = 'string'; // No type annotation
}


Compliant Example:export default class MyComponent extends LightningElement {
    myVar: string = 'string'; // Type annotation
}


Recommendation: Use TypeScript with explicit type annotations for all properties and methods.

12. Avoid Hardcoding URLs

Description: Hardcoded URLs in LWC make components non-portable and fragile across environments.
Non-compliant Example:const apiUrl = 'https://myorg.salesforce.com/api';


Compliant Example:import { getBaseUrl } from 'lightning/configProvider';
const apiUrl = `${getBaseUrl()}/api`;


Recommendation: Use Salesforce-provided utilities or custom metadata for URLs.

13. Ensure Accessibility Compliance

Description: LWC must follow accessibility standards (e.g., WCAG) to ensure usability for all users.
Non-compliant Example:<template>
    <button>Click me</button>
</template>


Compliant Example:<template>
    <button aria-label="Perform action">Click me</button>
</template>


Recommendation: Add ARIA attributes and test with accessibility tools.

14. Avoid Console Logs in Production

Description: console.log statements in LWC are meant for debugging and should not remain in production code.
Non-compliant Example:console.log('Component loaded');


Compliant Example:// Remove console.log or use a logging service


Recommendation: Use a logging framework or remove debug statements before deployment.

15. Optimize LWC Performance with @track and @api

Description: Incorrect use of @track or @api can lead to unnecessary re-renders or poor performance.
Non-compliant Example:export default class MyComponent extends LightningElement {
    myVar = { name: 'Test' }; // Not reactive
}


Compliant Example:export default class MyComponent extends LightningElement {
    @track myVar = { name: 'Test' }; // Reactive property
}


Recommendation: Use @track for complex objects and @api for public properties; minimize re-renders.

