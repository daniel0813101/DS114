#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node* next;
} Node;

extern Node* head;

void push_Back(int element);
void remove_Node(int element);
void update(int oldValue, int newValue);
void clean();
void invert_List();
void sort_List();

static void ta_append(int element) {
    Node* newNode = (Node*)malloc(sizeof(Node));
    newNode->data = element;
    newNode->next = NULL;

    if (head == NULL) {
        head = newNode;
        return;
    }

    Node* cur = head;
    while (cur->next != NULL) {
        cur = cur->next;
    }
    cur->next = newNode;
}

static void print_List_for_judge() {
    Node* cur = head;
    while (cur != NULL) {
        printf("%d", cur->data);
        if (cur->next != NULL) {
            printf(" ");
        }
        cur = cur->next;
    }
    printf("\n");
}

int main() {
    int n;
    scanf("%d", &n);

    for (int i = 0; i < n; i++) {
        char op;
        scanf(" %c", &op);

        if (op == 'b') {
            int x;
            scanf("%d", &x);
            push_Back(x);
        } else if (op == 'r') {
            int x;
            scanf("%d", &x);
            remove_Node(x);
        } else if (op == 'u') {
            int oldValue, newValue;
            scanf("%d %d", &oldValue, &newValue);
            update(oldValue, newValue);
        } else if (op == 'i') {
            invert_List();
        } else if (op == 's') {
            sort_List();
        } else if (op == 'C') {
            clean();
            printf("Clear the list!\n");
        } else if (op == 'a') {
            int x;
            scanf("%d", &x);
            ta_append(x);   // TA-only operation for isolated testing
        }
    }

    print_List_for_judge();
    clean();
    return 0;
}