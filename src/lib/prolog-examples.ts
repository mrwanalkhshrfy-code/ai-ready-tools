export interface PrologExample {
  id: string;
  title: string;
  titleAr: string;
  description: string;
  code: string;
  query: string;
}

export const prologExamples: PrologExample[] = [
  {
    id: "family",
    title: "Family Relations",
    titleAr: "العلاقات العائلية",
    description: "Facts and rules about family relationships",
    code: `% Family Relations - العلاقات العائلية
parent(tom, bob).
parent(tom, liz).
parent(bob, ann).
parent(bob, pat).

male(tom).
male(bob).
female(liz).
female(ann).
female(pat).

father(X, Y) :- parent(X, Y), male(X).
mother(X, Y) :- parent(X, Y), female(X).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
sibling(X, Y) :- parent(Z, X), parent(Z, Y), X \\= Y.`,
    query: "father(X, Y).",
  },
  {
    id: "animals",
    title: "Animal Classification",
    titleAr: "تصنيف الحيوانات",
    description: "Classify animals based on their properties",
    code: `% Animal Classification - تصنيف الحيوانات
has_feathers(eagle).
has_feathers(penguin).
has_fur(cat).
has_fur(dog).
has_scales(snake).

can_fly(eagle).
lays_eggs(eagle).
lays_eggs(penguin).
lays_eggs(snake).

bird(X) :- has_feathers(X), lays_eggs(X).
mammal(X) :- has_fur(X).
reptile(X) :- has_scales(X), lays_eggs(X).
flying_bird(X) :- bird(X), can_fly(X).`,
    query: "bird(X).",
  },
  {
    id: "list-ops",
    title: "List Operations",
    titleAr: "عمليات القوائم",
    description: "Common list operations in Prolog",
    code: `% List Operations - عمليات القوائم
my_member(X, [X|_]).
my_member(X, [_|T]) :- my_member(X, T).

my_append([], L, L).
my_append([H|T], L, [H|R]) :- my_append(T, L, R).

my_length([], 0).
my_length([_|T], N) :- my_length(T, N1), N is N1 + 1.

my_reverse([], []).
my_reverse([H|T], R) :- my_reverse(T, RT), my_append(RT, [H], R).

my_last(X, [X]).
my_last(X, [_|T]) :- my_last(X, T).`,
    query: "my_member(X, [1, 2, 3]).",
  },
  {
    id: "math",
    title: "Math & Recursion",
    titleAr: "الرياضيات والتكرار",
    description: "Factorial, Fibonacci, and math operations",
    code: `% Math & Recursion - الرياضيات والتكرار
factorial(0, 1).
factorial(N, F) :-
    N > 0,
    N1 is N - 1,
    factorial(N1, F1),
    F is N * F1.

fibonacci(0, 0).
fibonacci(1, 1).
fibonacci(N, F) :-
    N > 1,
    N1 is N - 1,
    N2 is N - 2,
    fibonacci(N1, F1),
    fibonacci(N2, F2),
    F is F1 + F2.

max(X, Y, X) :- X >= Y.
max(X, Y, Y) :- Y > X.

abs_val(X, X) :- X >= 0.
abs_val(X, Y) :- X < 0, Y is -X.`,
    query: "factorial(6, X).",
  },
  {
    id: "colors",
    title: "Map Coloring",
    titleAr: "تلوين الخرائط",
    description: "Graph coloring constraint problem",
    code: `% Map Coloring - تلوين الخرائط
color(red).
color(green).
color(blue).

colormap(A, B, C, D) :-
    color(A), color(B), color(C), color(D),
    A \\= B, A \\= C, A \\= D,
    B \\= C,
    C \\= D.`,
    query: "colormap(A, B, C, D).",
  },
  {
    id: "path",
    title: "Graph Search",
    titleAr: "البحث في الرسم البياني",
    description: "Find paths in a graph using search",
    code: `% Graph Search - البحث في الرسم البياني
edge(a, b).
edge(a, c).
edge(b, d).
edge(c, d).
edge(d, e).
edge(b, e).

path(X, X, [X]).
path(X, Y, [X|P]) :-
    edge(X, Z),
    path(Z, Y, P).`,
    query: "path(a, e, P).",
  },
];
