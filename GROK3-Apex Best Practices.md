# Salesforce Coding Best Practices Guide ( GROK 3 )

This guide outlines key best practices for developing secure, maintainable, and efficient Salesforce applications, based on CodeScan rules (version 25.1.3, September 2024). It covers Apex, Visualforce, Lightning, JavaScript, and Salesforce metadata, focusing on critical rules to ensure code quality and security.

## Apex Best Practices

### 1. Avoid Global Modifier (sf:AvoidGlobalModifier, MINOR, CODE_SMELL)
- **Description**: Using the `global` modifier in Apex classes or methods locks them in managed packages, hindering future modifications. Use `public` unless `global` is required for external access.
- **Non-compliant Example**:
  ```apex
  global class JobSyncScheduler implements Schedulable {
      global void execute(SchedulableContext ctx) {}
  }
  ```
- **Compliant Example**:
  ```apex
  public class JobSyncScheduler implements Schedulable {
      public void execute(SchedulableContext ctx) {}
  }
  ```
- **Recommendation**: Reserve `global` for APIs explicitly designed for external use.

### 2. Prevent SOQL Injection (sf:SOQLInjection, CRITICAL, VULNERABILITY)
- **Description**: Dynamic SOQL queries with unescaped user input can lead to SOQL injection vulnerabilities.
- **Non-compliant Example**:
  ```apex
  String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';
  Database.query(query);
  ```
- **Compliant Example**:
  ```apex
  String query = 'SELECT Id FROM Account WHERE Name = :userInput';
  Database.query(query);
  ```
- **Recommendation**: Use bind variables (`:variable`) or escape user input with `String.escapeSingleQuotes()`.

### 3. Avoid DML in Loops (sf:AvoidDMLInLoops, MAJOR, BUG)
- **Description**: Performing DML operations inside loops can hit Salesforce governor limits, causing runtime errors.
- **Non-compliant Example**:
  ```apex
  for (Account acc : accounts) {
      update acc;
  }
  ```
- **Compliant Example**:
  ```apex
  List<Account> toUpdate = new List<Account>();
  for (Account acc : accounts) {
      toUpdate.add(acc);
  }
  update toUpdate;
  ```
- **Recommendation**: Collect records in a list and perform DML outside the loop.

### 4. Avoid Hardcoding IDs (sf:AvoidHardcodingId, MAJOR, CODE_SMELL)
- **Description**: Hardcoding record IDs makes code non-portable across orgs and environments.
- **Non-compliant Example**:
  ```apex
  Account acc = [SELECT Id FROM Account WHERE Id = '001xxxxxxxxxxxx'];
  ```
- **Compliant Example**:
  ```apex
  Account acc = [SELECT Id FROM Account WHERE Name = 'Test Account'];
  ```
- **Recommendation**: Use queries or custom metadata to reference records dynamically.

### 5. Prevent XSS with escape=false (sf:ApexXssFromEscapeFalse, CRITICAL, VULNERABILITY)
- **Description**: Setting `escape=false` in Visualforce output can expose applications to cross-site scripting (XSS) attacks.
- **Non-compliant Example**:
  ```apex
  public String getContent() {
      return '<script>maliciousCode()</script>';
  }
  ```
- **Compliant Example**:
  ```apex
  public String getContent() {
      return String.escapeHtml4('<script>maliciousCode()</script>');
  }
  ```
- **Recommendation**: Use `escape=true` or sanitize output with `String.escapeHtml4()`.

### 6. Avoid Untrusted Input in Dynamic SOQL (sf:AvoidUntrustedInputDynamicSOQL, CRITICAL, VULNERABILITY)
- **Description**: Untrusted input in dynamic SOQL can lead to injection vulnerabilities.
- **Non-compliant Example**:
  ```apex
  String query = 'SELECT Id FROM Contact WHERE Email = \'' + userInput + '\'';
  ```
- **Compliant Example**:
  ```apex
  String query = 'SELECT Id FROM Contact WHERE Email = :userInput';
  ```
- **Recommendation**: Validate and sanitize all user inputs before using them in queries.

### 7. Ensure Unit Tests Have Asserts (sf:ApexUnitTestClassShouldHaveAsserts, MAJOR, CODE_SMELL)
- **Description**: Unit tests without assertions may not validate expected behavior, reducing test reliability.
- **Non-compliant Example**:
  ```apex
  @IsTest
  void testMethod() {
      Account acc = new Account(Name = 'Test');
      insert acc;
  }
  ```
- **Compliant Example**:
  ```apex
  @IsTest
  void testMethod() {
      Account acc = new Account(Name = 'Test');
      insert acc;
      System.assertEquals('Test', [SELECT Name FROM Account].Name);
  }
  ```
- **Recommendation**: Include `System.assert` or `Test.assertEquals` in all test methods.

### 8. Avoid Excessive Class Length (sf:AvoidExcessiveClassLength, MAJOR, CODE_SMELL)
- **Description**: Classes exceeding 1000 lines are hard to maintain and understand.
- **Non-compliant Example**:
  ```apex
  // 2000-line class with multiple responsibilities
  public class LargeClass { ... }
  ```
- **Compliant Example**:
  ```apex
  // Split into smaller, focused classes
  public class AccountService { ... }
  public class ContactService { ... }
  ```
- **Recommendation**: Refactor large classes into smaller, single-responsibility units.

## Visualforce & Lightning Best Practices

### 9. Disable Autocomplete for Password Fields (vf:PasswordAutocompleteCheck, MAJOR, VULNERABILITY)
- **Description**: Password fields without `autocomplete="off"` risk exposing sensitive data via browser autofill.
- **Non-compliant Example**:
  ```html
  <input type="password" name="pwd">
  ```
- **Compliant Example**:
  ```html
  <input type="password" name="pwd" autocomplete="off">
  ```
- **Recommendation**: Always set `autocomplete="off"` for password fields.

### 10. Avoid Inline JavaScript (vf:AvoidInlineJavaScript, MAJOR, VULNERABILITY)
- **Description**: Inline JavaScript in Visualforce or Lightning components can lead to XSS vulnerabilities.
- **Non-compliant Example**:
  ```html
  <apex:outputText value="{!data}" escape="false"/>
  ```
- **Compliant Example**:
  ```html
  <apex:outputText value="{!JSENCODE(data)}"/>
  ```
- **Recommendation**: Use `JSENCODE` or static resources for JavaScript.

### 11. Avoid Retired API Versions (vf:APIVersionsRetired, MAJOR, BUG)
- **Description**: Using retired API versions in Visualforce or Lightning can cause compatibility issues.
- **Non-compliant Example**:
  ```html
  <apex:page apiVersion="28.0">
  ```
- **Compliant Example**:
  ```html
  <apex:page apiVersion="59.0">
  ```
- **Recommendation**: Use the latest API version (e.g., 59.0 for Winter '25).

### 12. Ensure LWC TypeScript Compliance (vf:LWCTypeScriptSupport Stuart
- **Description**: LWC using TypeScript must follow Salesforce's TypeScript conventions for maintainability.
- **Non-compliant Example**:
  ```javascript
  // LWC with invalid TypeScript syntax
  export default class MyComponent {
      myVar = "string"; // Incorrect type annotation
  }
  ```
- **Compliant Example**:
  ```javascript
  export default class MyComponent {
      myVar: string = "string"; // Correct type annotation
  }
  ```
- **Recommendation**: Use proper TypeScript annotations and follow Salesforce LWC guidelines.

### 13. Avoid Session ID Exposure (vf:HotspotGetSessionIdUsage, MAJOR, SECURITY_HOTSPOT)
- **Description**: Using `GETSESSIONID()` or `$API.Session_Id` in Visualforce/LWC risks exposing session IDs to attackers.
- **Non-compliant Example**:
  ```html
  <script> var sessionId = "{!$API.Session_Id}"; </script>
  ```
- **Compliant Example**:
  ```html
  <!-- Avoid exposing session ID; use server-side logic -->
  ```
- **Recommendation**: Handle session-sensitive operations server-side.

## JavaScript Best Practices

### 14. Avoid Console Logs in Production (cs-js:no-console, MINOR, CODE_SMELL)
- **Description**: `console.log` or `console.error` calls in production code are meant for debugging and should be removed.
- **Non-compliant Example**:
  ```javascript
  console.log("Debug info");
  ```
- **Compliant Example**:
  ```javascript
  // Remove console.log or use a logging service
  ```
- **Recommendation**: Use proper logging mechanisms for production.

### 15. Prevent Hardcoded Passwords (javascript:S2068, CRITICAL, VULNERABILITY)
- **Description**: Hardcoding credentials in JavaScript exposes them to attackers.
- **Non-compliant Example**:
  ```javascript
  const password = "secret123";
  ```
- **Compliant Example**:
  ```javascript
  const password = process.env.PASSWORD; // Use environment variables
  ```
- **Recommendation**: Store sensitive data in environment variables or secure storage.

### 16. Avoid Complex Ternary Operators (javascript:S1774, MAJOR, CODE_SMELL)
- **Description**: Complex ternary operators reduce code readability.
- **Non-compliant Example**:
  ```javascript
  let result = condition ? value1 : condition2 ? value2 : value3;
  ```
- **Compliant Example**:
  ```javascript
  let result;
  if (condition) {
      result = value1;
  } else if (condition2) {
      result = value2;
  } else {
      result = value3;
  }
  ```
- **Recommendation**: Use `if-else` for complex logic.

### 17. Avoid Unsecure HTTP Requests (javascript:S5332, CRITICAL, VULNERABILITY)
- **Description**: Using HTTP instead of HTTPS for requests risks data interception.
- **Non-compliant Example**:
  ```javascript
  fetch("http://example.com/data");
  ```
- **Compliant Example**:
  ```javascript
  fetch("https://example.com/data");
  ```
- **Recommendation**: Always use HTTPS for external requests.

## Salesforce Metadata Best Practices

### 18. Restrict Profile Permissions (sfmeta:CustomProfilesPermission, CRITICAL, VULNERABILITY)
- **Description**: Granting "Modify All Data" to custom profiles risks data loss or corruption.
- **Non-compliant Example**:
  ```xml
  <userPermissions>
      <enabled>true</enabled>
      <name>ModifyAllData</name>
  </userPermissions>
  ```
- **Compliant Example**:
  ```xml
  <userPermissions>
      <enabled>false</enabled>
      <name>ModifyAllData</name>
  </userPermissions>
  ```
- **Recommendation**: Grant only necessary permissions in profiles.

### 19. Avoid Large Flows (sfmeta:AvoidLargeFlows, MINOR, CODE_SMELL)
- **Description**: Flows with excessive nodes are complex and hard to maintain.
- **Non-compliant Example**:
  ```xml
  <!-- Flow with 50+ nodes -->
  ```
- **Compliant Example**:
  ```xml
  <!-- Break into smaller sub-flows -->
  ```
- **Recommendation**: Use sub-flows to simplify complex flows.

### 20. Follow Flow Naming Conventions (sfmeta:FlowNaming, MINOR, CODE_SMELL)
- **Description**: Inconsistent flow names make maintenance difficult.
- **Non-compliant Example**:
  ```xml
  <fullName>flow1</fullName>
  ```
- **Compliant Example**:
  ```xml
  <fullName>Account_Validation_Flow</fullName>
  ```
- **Recommendation**: Use descriptive, consistent names (e.g., `[Object]_[Purpose]_Flow`).
