#include <iostream>
using namespace std;

struct Node {
    int data;
    Node* next;
    Node(int val) : data(val), next(nullptr) {}
};

extern Node* head;

void push_Back(int element);
void remove_Node(int element);
void update(int oldValue, int newValue);
void clean();
void invert_List();
void sort_List();

static void ta_append(int element) {
    Node* newNode = new Node(element);

    if (head == nullptr) {
        head = newNode;
        return;
    }

    Node* cur = head;
    while (cur->next != nullptr) {
        cur = cur->next;
    }
    cur->next = newNode;
}

static void print_List_for_judge() {
    Node* cur = head;
    while (cur != nullptr) {
        cout << cur->data;
        if (cur->next != nullptr) {
            cout << " ";
        }
        cur = cur->next;
    }
    cout << "\n";
}

int main() {
    int n;
    cin >> n;

    for (int i = 0; i < n; i++) {
        char op;
        cin >> op;

        if (op == 'b') {
            int x;
            cin >> x;
            push_Back(x);
        } else if (op == 'r') {
            int x;
            cin >> x;
            remove_Node(x);
        } else if (op == 'u') {
            int oldValue, newValue;
            cin >> oldValue >> newValue;
            update(oldValue, newValue);
        } else if (op == 'i') {
            invert_List();
        } else if (op == 's') {
            sort_List();
        } else if (op == 'C') {
            clean();
            cout << "Clear the list!\n";
        } else if (op == 'a') {
            int x;
            cin >> x;
            ta_append(x);   // TA-only operation for isolated testing
        }
    }

    print_List_for_judge();
    clean();
    return 0;
}