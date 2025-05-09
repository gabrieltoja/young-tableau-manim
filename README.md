# Implementing Young tableaus & partition bijections in Manim
Manim implementation of [Young's tableau](https://en.wikipedia.org/wiki/Young_tableau), a tool for visualizing partitions and partition bijections.
```
class YoungTableauDemonstration(Scene):
    def construct(self):
        young_tableau = YoungTableau(partition_sequence=np.array([3,7,9,5,7]))
        self.play(ShowCreation(young_tableau))
        self.play(SortingParts(young_tableau))
        self.play(FranklinInvoluting(young_tableau))
        self.play(Conjugating(young_tableau))
        self.play(Convoluting(young_tableau))
```
![](Demo.gif)
