class Nested {
    boolean accepts(int value) {
        if (value > 0) {
            if (value < 10) {
                if (value != 5) {
                    return true;
                }
            }
        }
        return false;
    }
}
