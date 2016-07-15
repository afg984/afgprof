void a() {
}


void b() {
    a();
}


void c() {
    a();
    b();
}


int main() {
    a();
    b();
    c();
}
