from .rational import Fraction, Constants as C
import itertools

class Poly(tuple):
    """Tuple polynomial class with rational coefficients and fast initialization.
    Automatically computes equality by comparing coefficients."""
    def __new__(cls, coefs):
        """Create new polynomial from coefficient list.
        Automatically removes trailing zeros on the right.
        If coefs = (c0,c1,...,cn), resulting polynomial is c0+c1*x+ ... +cn*x^n
        """
        internal = list(coefs)
        while internal and internal[-1] == 0:
            internal.pop()

        # zero polynomial still has length 1
        if len(internal) == 0:
            return super().__new__(cls, (C.n_0,))
        else:
            return super().__new__(cls, internal)

    def __hash__(self):
        # hash should identify equally with the coefficient, in the case the polynomial has degree 0
        if len(self) == 1:
            return hash(self[0])
        else:
            return super().__hash__()

    # TODO: string methods are total garbage (but they work)
    def _parse_coef_pair(self,r,n,symb="x",space=True):
        if r < 0:
            sgn = "-"
            num = f"{-r}"
        else:
            sgn = "+"
            num = str(r)

        if n == 0:
            op = ""
            right = ""
        else:
            if n == 1:
                right = symb
            else:
                right = f"{symb}^{n}"
            if r == 1 or r == -1:
                num = ""
                op = ""
            else:
                op = "*"

        if space:
            sgn = f" {sgn} "
        return sgn + num + op + right

    def with_symbol(self,symb,reverse=False,space=True):
        shift = 1 if space else 0
        if reverse:
            out = "".join(self._parse_coef_pair(r,n,symb,space=space) for n,r in reversed(enumerate(self)) if r != 0)[shift:]
        else:
            out = "".join(self._parse_coef_pair(r,n,symb,space=space) for n,r in enumerate(self) if r != 0)[shift:]
        if out.startswith('+'):
            return out[1+shift:]
        elif out.startswith('-'):
            return "-"+out[1+shift:]
        else:
            return "0"

    def __str__(self):
        return f"Poly({self.with_symbol('x')},x)"

    # -------------------------------
    # constructors
    # -------------------------------
    @classmethod
    def from_PurePoly(cls, pure_poly):
        coef_dct = pure_poly.as_dict()
        deg = max(coef_dct.keys())[0]
        lst = [C.n_0 for _ in range(deg+1)]
        for k,v in coef_dct.items():
            lst[k[0]] = Fraction(v.p,v.q)
        return Poly(lst)

    @classmethod
    def zero(cls):
        return super().__new__(cls, (C.n_0,))

    @classmethod
    def one(cls):
        return super().__new__(cls, (C.n_1,))

    @classmethod
    def cnst(cls, cnst):
        return super().__new__(cls, (cnst,))

    @classmethod
    def monomial(cls, n, coef=C.n_1):
        return super().__new__(cls, [C.n_0]*n+[coef])

    # -------------------------------
    # properties
    # -------------------------------
    @property
    def deg(self):
        return len(self)-1

    @property
    def leading(self):
        return self[-1]

    @property
    def constant(self):
        return self[0]

    # -------------------------------
    # mathematical operations
    # -------------------------------
    def __add__(self,other):
        return Poly(a+b for a,b in itertools.zip_longest(self,other,fillvalue=C.n_0))

    def __sub__(self,other):
        return Poly(a-b for a,b in itertools.zip_longest(self,other,fillvalue=C.n_0))

    def __mul__(self,other):
        return self.add_iter(Poly.monomial(n+m, c1*c2) for (n, c1), (m, c2) in itertools.product(enumerate(self),enumerate(other)))

    def __neg__(self):
        return self.mul_cnst(-C.n_1)

    def eval(self, value):
        return sum(coef*value**n for n,coef in enumerate(self) if coef != 0)

    # -------------------------------
    # internal multipliation helpers
    # -------------------------------
    def mul_cnst(self,cnst):
        return Poly(cnst*x for x in self)

    def mul_monom(self, n):
        "multiply the self by a monomial of degree n"
        return Poly(tuple(C.n_0 for _ in range(n)) + self)

    @staticmethod
    def add_iter(polys):
        "add an iterable of polynomials"
        return Poly(sum(vals) for vals in itertools.zip_longest(*polys,fillvalue=C.n_0))

    # -------------------------------
    # modulo methods
    # -------------------------------
    def rem(self, poly):
        """Compute the remainder of self (modulo poly)"""
        while self.deg >= poly.deg:
            self = self - poly.mul_cnst(self.leading/poly.leading).mul_monom(self.deg-poly.deg)
        return self

    def div(self,poly):
        """Returns q,r so that self=q*poly + r"""
        intm = [C.n_0 for _ in range(self.deg - poly.deg+1)]
        if poly.deg == 0:
            return self.mul_cnst(C.n_1/poly.leading), Poly.zero()
        while self.deg >= poly.deg:
            intm[self.deg-poly.deg] = self.leading/poly.leading
            self = self - poly.mul_cnst(self.leading/poly.leading).mul_monom(self.deg-poly.deg)
        return Poly(intm), self

    def gcdex(self, other):
        """Returns p1,p2,g so that g=gcd(self,other) and self*p1 + other*p2 = g"""
        s = Poly.zero()
        old_s = Poly.one()
        t = Poly.one()
        old_t = Poly.zero()
        r = other
        old_r = self
    
        while r != Poly.zero():
            quotient, rem = old_r.div(r)
            old_r, r = r, rem
            old_s, s = s, old_s - quotient * s
            old_t, t = t, old_t - quotient * t
        
        # normalize to monic gcd
        nm = C.n_1/old_r.leading
        return old_s.mul_cnst(nm),old_t.mul_cnst(nm),old_r.mul_cnst(nm)

    def invert(self, other):
        """Returns p1 so that and self*p1 = gcd(self,other) modulo other"""
        s = Poly.zero()
        old_s = Poly.one()
        r = other
        old_r = self
    
        while r != Poly.zero():
            quotient, rem = old_r.div(r)
            old_r, r = r, rem
            old_s, s = s, old_s - quotient * s

        # normalize to monic gcd
        nm = C.n_1/old_r.leading
        return old_s.mul_cnst(nm)

