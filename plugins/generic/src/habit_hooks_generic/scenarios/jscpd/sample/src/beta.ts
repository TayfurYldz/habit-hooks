export function beta(x: number, y: number) {
  const sum = x + y;
  const product = x * y;
  const diff = x - y;
  const quotient = x / y;
  const scaled = sum * product;
  const shifted = diff - quotient;
  const blended = scaled + shifted;
  return { sum, product, diff, quotient, scaled, shifted, blended };
}
