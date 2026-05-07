#include <iostream>
#include <queue>
using namespace std;

struct Node {
    int data;
    Node* left;
    Node* right;

    Node(int val) : data(val), left(nullptr), right(nullptr) {}
};

Node* buildTree(int arr[], int n);
void inorder(Node* root);
void preorder(Node* root);
void postorder(Node* root);
int countRounds(Node* root);
int totalPrizeToTarget(Node* root, int target);

static Node* ta_buildTree(int arr[], int n) {
    if (n == 0 || arr[0] == -1) return nullptr;

    Node* root = new Node(arr[0]);
    queue<Node*> q;
    q.push(root);

    int i = 1;

    while (!q.empty() && i < n) {
        Node* cur = q.front();
        q.pop();

        if (i < n && arr[i] != -1) {
            cur->left = new Node(arr[i]);
            q.push(cur->left);
        }
        i++;

        if (i < n && arr[i] != -1) {
            cur->right = new Node(arr[i]);
            q.push(cur->right);
        }
        i++;
    }

    return root;
}

static void deleteTree(Node* root) {
    if (root == nullptr) return;

    deleteTree(root->left);
    deleteTree(root->right);
    delete root;
}

int main() {
    int mode;
    cin >> mode;

    int n;
    cin >> n;

    int arr[105];
    for (int i = 0; i < n; i++) {
        cin >> arr[i];
    }

    int target;
    cin >> target;

    Node* root = nullptr;

    if (mode == 1) {
        // Test student's buildTree()
        root = buildTree(arr, n);
    } else {
        // TA-only correct builder for isolated testing
        root = ta_buildTree(arr, n);
    }

    inorder(root);
    cout << "\n";

    preorder(root);
    cout << "\n";

    postorder(root);
    cout << "\n";

    cout << countRounds(root) << "\n";
    cout << totalPrizeToTarget(root, target) << "\n";

    deleteTree(root);
    return 0;
}