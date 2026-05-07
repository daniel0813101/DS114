#include <stdio.h>
#include <stdlib.h>

typedef struct Node {
    int data;
    struct Node* left;
    struct Node* right;
} Node;

Node* buildTree(int arr[], int n);
void inorder(Node* root);
void preorder(Node* root);
void postorder(Node* root);
int countRounds(Node* root);
int totalPrizeToTarget(Node* root, int target);

static Node* ta_createNode(int val) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->data = val;
    node->left = NULL;
    node->right = NULL;
    return node;
}

static Node* ta_buildTree(int arr[], int n) {
    if (n == 0 || arr[0] == -1) return NULL;

    Node* root = ta_createNode(arr[0]);

    Node* q[105];
    int front = 0;
    int rear = 0;

    q[rear++] = root;

    int i = 1;

    while (front < rear && i < n) {
        Node* cur = q[front++];

        if (i < n && arr[i] != -1) {
            cur->left = ta_createNode(arr[i]);
            q[rear++] = cur->left;
        }
        i++;

        if (i < n && arr[i] != -1) {
            cur->right = ta_createNode(arr[i]);
            q[rear++] = cur->right;
        }
        i++;
    }

    return root;
}

static void deleteTree(Node* root) {
    if (root == NULL) return;

    deleteTree(root->left);
    deleteTree(root->right);
    free(root);
}

int main() {
    int mode;
    scanf("%d", &mode);

    int n;
    scanf("%d", &n);

    int arr[105];
    for (int i = 0; i < n; i++) {
        scanf("%d", &arr[i]);
    }

    int target;
    scanf("%d", &target);

    Node* root = NULL;

    if (mode == 1) {
        // Test student's buildTree()
        root = buildTree(arr, n);
    } else {
        // TA-only correct builder for isolated testing
        root = ta_buildTree(arr, n);
    }

    inorder(root);
    printf("\n");

    preorder(root);
    printf("\n");

    postorder(root);
    printf("\n");

    printf("%d\n", countRounds(root));
    printf("%d\n", totalPrizeToTarget(root, target));

    deleteTree(root);
    return 0;
}