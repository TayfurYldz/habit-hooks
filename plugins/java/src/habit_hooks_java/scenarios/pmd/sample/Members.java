class Members {
    private int staleField = 1;
    private int liveField = 2;
    private void staleMethod() {}
    private int liveMethod() { return liveField; }
    int value() { return liveMethod(); }
}
