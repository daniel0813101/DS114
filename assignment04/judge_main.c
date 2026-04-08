#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

typedef struct Node {
    int data;
    struct Node* next;
} Node;

extern Node* head;

void push_Back(int element);
void push_Front(int element);
void remove_Node(int element);
bool contain(int element);
void invert_List();
void clean();

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
    int n, x;
    char op;

    scanf("%d", &n);

    for (int i = 0; i < n; i++) {
        scanf(" %c", &op);

        if (op == 'b') {
            scanf("%d", &x);
            push_Back(x);
        } else if (op == 'f') {
            scanf("%d", &x);
            push_Front(x);
        } else if (op == 'r') {
            scanf("%d", &x);
            remove_Node(x);
        } else if (op == 'c') {
            scanf("%d", &x);
            printf("%s\n", contain(x) ? "True" : "False");
        } else if (op == 'i') {
            invert_List();
        } else if (op == 'C') {
            clean();
            printf("Clear the list!\n");
        } else if (op == 'a') {
            scanf("%d", &x);
            ta_append(x);   // TA-only operation for isolated testing
        }
    }

    print_List_for_judge();
    clean();
    return 0;
}