# Salesforce Apex and LWC Best Practices

## Apex Best Practices

### 1. **Bulkification**
- **Why**: Salesforce operates in a multi-tenant environment with governor limits (e.g., 100 SOQL queries per transaction). Bulkification ensures code handles multiple records efficiently.
- **How**:
  - Use collections (Lists, Sets, Maps) to process records in bulk.
  - Avoid SOQL queries or DML operations inside loops.
  - Example:
    ```apex
    // Bad: SOQL in loop
    for (Account acc : accounts) {
        Contact c = [SELECT Id FROM Contact WHERE AccountId = :acc.Id LIMIT 1];
    }

    // Good: Bulkified SOQL
    Set<Id> accountIds = new Set<Id>();
    for (Account acc : accounts) {
        accountIds.add(acc.Id);
    }
    Map<Id, Contact> contacts = new Map<Id, Contact>([SELECT Id, AccountId FROM Contact WHERE AccountId IN :accountIds]);
    ```

### 2. **Modular and Reusable Code**
- **Why**: Promotes maintainability and reduces code duplication.
- **How**:
  - Use helper classes or service layers to encapsulate business logic.
  - Follow the **Single Responsibility Principle (SRP)**: Each class/method should have one purpose.
  - Example:
    ```apex
    public class AccountService {
        public static void updateAccountStatus(List<Account> accounts) {
            for (Account acc : accounts) {
                acc.Status__c = 'Processed';
            }
        }
    }
    ```

### 3. **Trigger Frameworks**
- **Why**: Triggers can become complex and hard to maintain. A framework ensures consistency and avoids recursive calls.
- **How**:
  - Use a trigger handler pattern to centralize logic.
  - Implement a single trigger per object to avoid order-of-execution issues.
  - Use a trigger dispatcher to manage execution flow.
  - Example (Trigger Handler Pattern):
    ```apex
    // AccountTrigger.trigger
    trigger AccountTrigger on Account (before insert, after insert, before update, after update) {
        AccountTriggerHandler.handleTrigger(Trigger.new, Trigger.oldMap, Trigger.operationType);
    }

    // AccountTriggerHandler.cls
    public class AccountTriggerHandler {
        public static void handleTrigger(List<Account> newRecords, Map<Id, Account> oldMap, System.TriggerOperation op) {
            switch on op {
                when BEFORE_INSERT {
                    beforeInsert(newRecords);
                }
                when AFTER_UPDATE {
                    afterUpdate(newRecords, oldMap);
                }
            }
        }

        private static void beforeInsert(List<Account> newRecords) {
            // Logic for before insert
        }

        private static void afterUpdate(List<Account> newRecords, Map<Id, Account> oldMap) {
            // Logic for after update
        }
    }
    ```

### 4. **Exception Handling**
- **Why**: Proper exception handling ensures robust code and meaningful error messages for users and developers.
- **How**:
  - Use try-catch blocks for operations prone to errors (e.g., DML, SOQL).
  - Log errors using custom objects or Platform Events for debugging.
  - Throw custom exceptions for specific scenarios.
  - Example:
    ```apex
    public class CustomException extends Exception {}

    public static void processAccounts(List<Account> accounts) {
        try {
            update accounts;
        } catch (DmlException e) {
            Error_Log__c log = new Error_Log__c(
                Message__c = e.getMessage(),
                Stack_Trace__c = e.getStackTraceString()
            );
            insert log;
            throw new CustomException('Failed to update accounts: ' + e.getMessage());
        }
    }
    ```

### 5. **Governor Limits Awareness**
- **Why**: Salesforce imposes strict governor limits (e.g., SOQL, DML, CPU time).
- **How**:
  - Use `Limits` class to monitor usage (e.g., `Limits.getQueries()`).
  - Cache data in static variables or Maps to reduce SOQL queries.
  - Use asynchronous processing (@future, Queueable, Batch) for heavy operations.
  - Example:
    ```apex
    public class BatchUpdateAccounts implements Database.Batchable<sObject> {
        public Database.QueryLocator start(Database.BatchableContext bc) {
            return Database.getQueryLocator('SELECT Id FROM Account WHERE Status__c = \'Pending\'');
        }

        public void execute(Database.BatchableContext bc, List<Account> scope) {
            for (Account acc : scope) {
                acc.Status__c = 'Processed';
            }
            update scope;
        }

        public void finish(Database.BatchableContext bc) {}
    }
    ```

### 6. **Security Best Practices**
- **Why**: Protects data and ensures compliance with Salesforce security standards.
- **How**:
  - Enforce CRUD/FLS (Create, Read, Update, Delete/Field-Level Security) using `isAccessible()`, `isCreateable()`, etc.
  - Use `WITH SECURITY_ENFORCED` in SOQL queries.
  - Sanitize user inputs to prevent SOQL/SOSL injection.
  - Example:
    ```apex
    if (Schema.sObjectType.Account.fields.Name.isAccessible()) {
        List<Account> accounts = [SELECT Name FROM Account WHERE Id = :accountId WITH SECURITY_ENFORCED];
    }
    ```

### 7. **Testing Best Practices**
- **Why**: Apex requires 75% code coverage, but tests should also validate functionality.
- **How**:
  - Write meaningful unit tests that test both positive and negative scenarios.
  - Use `Test.startTest()` and `Test.stopTest()` to isolate test execution.
  - Mock external dependencies using `HttpCalloutMock` or dependency injection.
  - Example:
    ```apex
    @isTest
    private class AccountServiceTest {
        @isTest
        static void testUpdateAccountStatus() {
            Account acc = new Account(Name = 'Test Account', Status__c = 'Pending');
            insert acc;

            Test.startTest();
            AccountService.updateAccountStatus(new List<Account>{acc});
            Test.stopTest();

            acc = [SELECT Status__c FROM Account WHERE Id = :acc.Id];
            System.assertEquals('Processed', acc.Status__c, 'Status should be updated');
        }
    }
    ```

## LWC Best Practices

### 1. **Component Modularity**
- **Why**: Modular components are reusable, maintainable, and easier to test.
- **How**:
  - Break down complex UIs into smaller, reusable components.
  - Use composition to combine components (e.g., parent-child components).
  - Example:
    ```html
    <!-- parentComponent.html -->
    <template>
        <c-child-component record-id={recordId}></c-child-component>
    </template>
    ```

### 2. **Use Lightning Data Service (LDS)**
- **Why**: LDS provides a declarative way to interact with Salesforce data, reducing Apex calls.
- **How**:
  - Use `lightning-record-form`, `lightning-record-edit-form`, or `@wire` with `getRecord`.
  - Cache data to minimize server calls.
  - Example:
    ```javascript
    // childComponent.js
    import { LightningElement, api, wire } from 'lwc';
    import { getRecord } from 'lightning/uiRecordApi';
    import ACCOUNT_NAME_FIELD from '@salesforce/schema/Account.Name';

    export default class ChildComponent extends LightningElement {
        @api recordId;
        @wire(getRecord, { recordId: '$recordId', fields: [ACCOUNT_NAME_FIELD] })
        account;
    }
    ```

### 3. **Asynchronous Apex Calls**
- **Why**: Improves performance by handling server calls efficiently.
- **How**:
  - Use `@AuraEnabled(cacheable=true)` for read-only Apex methods called via `@wire`.
  - Handle errors gracefully in the UI.
  - Example:
    ```javascript
    // myComponent.js
    import { LightningElement, wire } from 'lwc';
    import getAccounts from '@salesforce/apex/AccountController.getAccounts';

    export default class MyComponent extends LightningElement {
        @wire(getAccounts)
        accounts({ error, data }) {
            if (data) {
                this.accounts = data;
            } else if (error) {
                this.showToast('Error', error.body.message, 'error');
            }
        }
    }
    ```

### 4. **Error Handling in LWC**
- **Why**: Ensures a good user experience and robust debugging.
- **How**:
  - Use `try-catch` for imperative Apex calls.
  - Display user-friendly messages using `lightning-toast` or `lightning-messages`.
  - Example:
    ```javascript
    import { LightningElement } from 'lwc';
    import saveRecord from '@salesforce/apex/MyController.saveRecord';

    export default class MyComponent extends LightningElement {
        async handleSave() {
            try {
                await saveRecord({ record: this.record });
                this.showToast('Success', 'Record saved!', 'success');
            } catch (error) {
                this.showToast('Error', error.body.message, 'error');
            }
        }

        showToast(title, message, variant) {
            const evt = new ShowToastEvent({ title, message, variant });
            this.dispatchEvent(evt);
        }
    }
    ```

### 5. **Event-Driven Architecture**
- **Why**: Decouples components and enables communication between parent and child components.
- **How**:
  - Use custom events for child-to-parent communication.
  - Use `pubsub` or `Lightning Message Service (LMS)` for cross-component communication.
  - Example (Custom Event):
    ```javascript
    // childComponent.js
    export default class ChildComponent extends LightningElement {
        handleClick() {
            const event = new CustomEvent('recordselected', { detail: this.recordId });
            this.dispatchEvent(event);
        }
    }

    // parentComponent.js
    export default class ParentComponent extends LightningElement {
        handleRecordSelected(event) {
            this.selectedRecordId = event.detail;
        }
    }
    ```

### 6. **Performance Optimization**
- **Why**: Improves user experience and adheres to Salesforce’s performance guidelines.
- **How**:
  - Use `@track` only when necessary; rely on reactive properties.
  - Minimize DOM updates by batching changes.
  - Lazy-load data using infinite scrolling or pagination.
  - Example (Pagination):
    ```javascript
    import { LightningElement, wire } from 'lwc';
    import getPagedAccounts from '@salesforce/apex/AccountController.getPagedAccounts';

    export default class PaginatedAccounts extends LightningElement {
        pageNumber = 1;
        pageSize = 10;

        @wire(getPagedAccounts, { pageNumber: '$pageNumber', pageSize: '$pageSize' })
        accounts;

        handleNext() {
            this.pageNumber++;
        }
    }
    ```

### 7. **Testing LWC**
- **Why**: Ensures components work as expected and are maintainable.
- **How**:
  - Use Jest for unit testing LWC components.
  - Mock Apex calls and LDS responses.
  - Test user interactions and edge cases.
  - Example:
    ```javascript
    // myComponent.test.js
    import { createElement } from 'lwc';
    import MyComponent from 'c/myComponent';
    import getAccounts from '@salesforce/apex/AccountController.getAccounts';

    jest.mock('@salesforce/apex/AccountController.getAccounts');

    describe('MyComponent', () => {
        it('displays accounts from Apex', async () => {
            const mockAccounts = [{ Id: '001', Name: 'Test Account' }];
            getAccounts.mockResolvedValue(mockAccounts);

            const element = createElement('c-my-component', { is: MyComponent });
            document.body.appendChild(element);

            await Promise.resolve();
            const accountElements = element.shadowRoot.querySelectorAll('.account');
            expect(accountElements.length).toBe(1);
        });
    });
    ```

## Design Patterns for Apex and LWC

### 1. **Service Layer Pattern (Apex)**
- Centralizes business logic in a dedicated service class.
- Example:
  ```apex
  public class OpportunityService {
      public static void closeOpportunities(List<Opportunity> opps) {
          for (Opportunity opp : opps) {
              opp.StageName = 'Closed Won';
          }
          update opps;
      }
  }
  ```

### 2. **Repository Pattern (Apex)**
- Encapsulates data access logic for reusability and testability.
- Example:
  ```apex
  public class AccountRepository {
      public static List<Account> getAccountsByIds(Set<Id> accountIds) {
          return [SELECT Id, Name FROM Account WHERE Id IN :accountIds WITH SECURITY_ENFORCED];
      }
  }
  ```

### 3. **Facade Pattern (Apex/LWC)**
- Simplifies complex subsystem interactions for LWC components.
- Example:
  ```apex
  public class AccountFacade {
      @AuraEnabled(cacheable=true)
      public static Account getAccountDetails(Id accountId) {
          return AccountRepository.getAccountsByIds(new Set<Id>{accountId})[0];
      }
  }
  ```

### 4. **Publisher-Subscriber Pattern (LWC)**
- Use LMS for loosely coupled communication between components.
- Example:
  ```javascript
  // publisher.js
  import { publish, MessageContext } from 'lightning/messageService';
  import MY_CHANNEL from '@salesforce/messageChannel/MyChannel__c';

  export default class Publisher extends LightningElement {
      @wire(MessageContext) messageContext;
      publishMessage() {
          publish(this.messageContext, MY_CHANNEL, { recordId: this.recordId });
      }
  }

  // subscriber.js
  import { subscribe, MessageContext } from 'lightning/messageService';
  import MY_CHANNEL from '@salesforce/messageChannel/MyChannel__c';

  export default class Subscriber extends LightningElement {
      @wire(MessageContext) messageContext;
      subscription = null;

      connectedCallback() {
          this.subscription = subscribe(this.messageContext, MY_CHANNEL, (message) => {
              this.handleMessage(message);
          });
      }
  }
  ```

## Additional Recommendations
- **Code Documentation**: Use clear comments and ApexDoc for methods and classes.
- **Version Control**: Use Git with meaningful commit messages.
- **Naming Conventions**: Follow camelCase for Apex and kebab-case for LWC files.
- **Accessibility**: Ensure LWC components are accessible (e.g., use ARIA attributes).
- **Deployment**: Use Salesforce CLI and metadata API for consistent deployments.
