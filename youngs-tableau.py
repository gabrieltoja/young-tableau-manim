from manimlib.imports import *
import numpy as np

class YoungTableau(VGroup):
    def __init__(self, partition_sequence, padding = .3, center_x = 0, center_y = 0, color = WHITE, shape = "circle"):
        assert shape in ["circle", "young", "young", "square"]
        self.color = color
        self.partition_sequence = partition_sequence
        self.constituent_shapes = [];
        VGroup.__init__(self)
        for i in range(np.size(partition_sequence)):
             cell = partition_sequence[i]
             for j in range(cell):
                if shape == "square" or shape == "young":
                    dot = Square(side_length=padding).set_color(color)
                else:
                    dot = Dot().set_color(color)
                dot.location = (i,j) # (down, right)
                dot.layer = min(i, j)
                dot.row_length = cell
                self.constituent_shapes.append(dot)
                dot.move_to(np.array([center_x - .5 * padding * np.max(partition_sequence) + padding * j, center_y - .5 * padding * np.size(partition_sequence) + padding * (np.size(partition_sequence)-i), 0]))
                self.add(dot)
        self.coordinate_dictionary = self.updateDictionary()
        self.corner = self.updateCornerPosition()
        self.padding = self.updatePaddingDistance()
        self.parts = self.updateParts()
    def updateLayers(self):
        # check that the Young's diagram actually has continuous layers.
        for i in range(len(self.partition_sequence)):
            if (self.partition_sequence[i] < i):
                for j in [k+i+1 for k in range(len(self.partition_sequence)-i-1)]:
                    if (self.partition_sequence[j] > self.partition_sequence[i]):
                        raise Exception("⚠️ Attempted to find 'layers' for a partition ", self.partition_sequence, " with fragmented layer ", self.partition_sequence[j], ". Consider sorting the array.")
        diagonals = []
        for dot in self.constituent_shapes:
            if dot.location[0] == dot.location[1]:
                diagonals.append(dot)
        number_of_layers = len(diagonals)
        layers = [[] for i in range(number_of_layers)]
        for dot in self.constituent_shapes:
            dot.layer = min(dot.location[0], dot.location[1])
            layers[dot.layer].append(dot)
        # update position_in_layer attribute for dots.
        def ahead_of_me(dot, first, second):
            if dot.location[0] > first:
                return 1 # true if lower
            elif dot.location[1] < second:
                return 1 # true if further left
            else:
                return 0
        for layer in layers:
            for dot in layer:
                list_of_dots_ahead_of_me_in_a_layer = list(filter(lambda x: ahead_of_me(x, dot.location[0], dot.location[1]), layer))
                dot.position_in_layer = len(list_of_dots_ahead_of_me_in_a_layer)
        self.layers = layers
        return layers
    def updateDictionary(self):
        # relies on accurate location properties for every dot.
        new_dict = {}
        for dot in self.constituent_shapes:
            new_dict[dot.location] = dot
        self.coordinate_dictionary = new_dict
        return new_dict
    def updateCornerPosition(self):
        # relies on accurate location property for the corner dot.
        return self.coordinate_dictionary[(0,0)].get_center()
    def updatePaddingDistance(self):
        self.updateDictionary()
        try:
            self.padding = abs(
                self.coordinate_dictionary[(0, 1)].get_center()[0] - self.coordinate_dictionary[(0, 0)].get_center()[0])
        except Exception:
            try:
                self.padding = abs(
                    self.coordinate_dictionary[(1, 0)].get_center()[1] -
                    self.coordinate_dictionary[(0, 0)].get_center()[1])
            except Exception("There was no adjacent dot to the corner dot, so distances couldn't be computed."):
                return 0
        self.RELATIVE_RIGHT = self.padding*RIGHT
        self.RELATIVE_DOWN = self.padding*DOWN
        return self.padding
    def updateParts(self):
        # relies on accurate partition sequence, and accurate locations.
        parts = [[] for i in range(len(self.partition_sequence))]
        for dot in self.constituent_shapes:
            dot.part = dot.location[0]
            parts[dot.part].append(dot)
        self.parts = parts
        return parts
    def updatePartitionSequence(self):
        number_of_parts = max(self.constituent_shapes, key=lambda dot: dot.location[0])
        new_partition_sequence = [0]*(number_of_parts.location[0]+1)
        for dot in self.constituent_shapes:
            new_partition_sequence[dot.location[0]] += 1
        self.partition_sequence = new_partition_sequence
        return new_partition_sequence

class _ShiftALayerOnce(AnimationGroup):
    CONFIG = {
        "run_time": .5
    }
    def __init__(self, young, layer_to_shift):
        self.check_if_input_is_young_tableau(young)
        animations = []
        layer = young.layers[layer_to_shift]
        for reference_dot in layer:
            next_dot = [dot for dot in layer if dot.position_in_layer == reference_dot.position_in_layer+1]
            if next_dot:
                animations.append(ApplyMethod(reference_dot.move_to, next_dot[0]))
            else:
                animations.append(ApplyMethod(reference_dot.shift, young.RELATIVE_RIGHT))
        super().__init__(*animations)
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")

class _ShiftALayerCompletely(Succession):
    def __init__(self, young, layer_to_shift):
        self.check_if_input_is_young_tableau(young)
        if max([dot.location[0] for dot in young.layers[layer_to_shift]])-layer_to_shift > 0:
            animations = [
                _ShiftALayerOnce(young, layer_to_shift) for i in range(max([dot.location[0] for dot in young.layers[layer_to_shift]])-layer_to_shift)
            ]
        else:
            young.updateLayers()
            animations = [ScaleInPlace(young, 1)]
        super().__init__(*animations)
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")

class _Justify(AnimationGroup):
    def __init__(self, young):
        self.check_if_input_is_young_tableau(young)
        animations = []
        for layer in young.layers:
            for dot in layer:
                animations.append(ApplyMethod(dot.shift, young.RELATIVE_RIGHT*(-dot.layer)))
        super().__init__(*animations)
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")

class SortingParts(AnimationGroup):
    def __init__(self, young):
        self.check_if_input_is_young_tableau(young)
        young.updatePaddingDistance()
        animations = []
        if list(young.partition_sequence) == sorted(list(young.partition_sequence), reverse=True):
            print("⚠️ Warning: sorting an array with a partition sequence that is already sorted")
        else:
            print(str(list(young.partition_sequence)), "is being sorted to", str(sorted(list(young.partition_sequence), reverse=True)))
            young.partition_sequence = sorted(list(young.partition_sequence), reverse=True)
            parts = young.parts
            rank = 0
            for i in range(max(young.partition_sequence)+1):
                for part_index in range(len(young.parts)):
                    if len(parts[part_index]) == i:
                        original_rank = len(parts) - part_index
                        rank += 1
                        difference = original_rank - rank
                        partgroup = VGroup()
                        for dot in parts[part_index]:
                            dot.location = (len(parts)-rank, dot.location[1])
                            partgroup.add(dot)
                        animations.append(ApplyMethod(partgroup.shift, difference*young.RELATIVE_DOWN))
            young.updateLayers()
            young.updateCornerPosition()
            young.updateDictionary()
            young.updateParts()
        super().__init__(*animations)
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")

class Convoluting(Succession):
    def __init__(self, young):
        self.check_if_input_is_young_tableau(young)
        if len(young.partition_sequence)<2 or (max(young.partition_sequence))<2:
            raise Exception("⚠️ Convolution cannot be performed on partitions with fewer than two parts or with a maximum part size less than two")
        young.updatePaddingDistance()
        young.updateLayers()
        new_partition_sequence = []
        for i in range(len(young.layers)):
            new_partition_sequence.append(len(young.layers[i]))
        print(young.partition_sequence, "is convolving to", new_partition_sequence)
        young.partition_sequence = new_partition_sequence
        animations = [
            _ShiftALayerCompletely(young, i) for i in range(len(young.layers))
        ]
        animations.append(_Justify(young))
        for dot in young.constituent_shapes:
            dot.location = (dot.layer, dot.position_in_layer)
            dot.layer = min(dot.location[0], dot.location[1])
        young.updateLayers()
        young.updateCornerPosition()
        young.updateDictionary()
        young.updateParts()
        super().__init__(*animations)
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")

class Conjugating(Rotating):
    CONFIG = {
        "run_time": .5,
        "rate_func": linear,
        "about_edge": None,
    }
    def __init__(self, young):
        self.mobject = young
        partition_sequence = young.partition_sequence
        # update the diagram's partition_sequence property so it accurately reflects the conjugation
        conjugated_partition_sequence = []
        for i in range(max(partition_sequence)):
            conjugated_partition_sequence.append(sum(part > i for part in partition_sequence))
        print(list(young.partition_sequence), "is conjugating to", conjugated_partition_sequence)
        young.partition_sequence = conjugated_partition_sequence
        # update the location property for every dot.
        for dot in young.constituent_shapes:
            dot.location = dot.location[::-1]
        # update the coordinate dictionary based on each dots location.
        young.updateDictionary()
        young.updateParts()
    def check_if_input_is_young_tableau(self, young):
        if not isinstance(young, YoungTableau):
            raise Exception("Convolution must take in a Young's Diagram object")
    def interpolate_mobject(self, alpha):
        self.mobject.become(self.starting_mobject)
        self.mobject.rotate(
            alpha * TAU/2,
            axis=np.array([1,-1,0]),
            about_point=self.mobject.updateCornerPosition(),
            about_edge=self.about_edge,
        )

class FranklinInvoluting(AnimationGroup):
    def __init__(self, young):
        if not list(young.partition_sequence) == sorted(list(young.partition_sequence), reverse=True):
            raise Exception("Young's diagram must be sorted for a visual display of Franklin involution. Consider running the sorting animation first.")
        animations = [ScaleInPlace(young, 1)]
        self.mobject = young
        young.updatePaddingDistance()
        partition_sequence = young.partition_sequence
        diagonal_group = VGroup()
        # populate diagonal group with the (continuous) right diagonal.
        for part_num, part_size in enumerate(partition_sequence):
            if part_num == 0 or partition_sequence[part_num] == partition_sequence[part_num-1]-1:
                diagonal_group.add(young.coordinate_dictionary[(part_num, part_size-1)])
            else:
                diagonal_group.length = part_num
                break
        # get the bottom part and its length.
        bottom_group = VGroup()
        for dot in young.parts[len(partition_sequence)-1]:
            bottom_group.add(dot)
            bottom_group.length = len(young.parts[len(partition_sequence)-1])
        if (bottom_group.length == diagonal_group.length or bottom_group.length == diagonal_group.length+1) and diagonal_group.length == len(partition_sequence):
            print("Franklin involuting does nothing for this partition")
            intersecting_dot = young.coordinate_dictionary[(len(partition_sequence), min(partition_sequence))]
        elif diagonal_group.length > bottom_group.length:
            # move bottom group along the diagonal
            landing_strip = VGroup()
            for dot in diagonal_group:
                if dot.location[0] < bottom_group.length:
                    landing_strip.add(dot)
            animations.append(ApplyMethod(bottom_group.move_to, landing_strip.get_center()+young.RELATIVE_RIGHT))
            for dot in bottom_group:
                target_part_num = bottom_group.length - 1 - dot.location[1]
                target_part_size = len(young.parts[target_part_num])-1
                animations.append(ApplyMethod(dot.move_to, young.coordinate_dictionary[(target_part_num, target_part_size)].get_center() + young.RELATIVE_RIGHT))
                dot.location = (target_part_num, target_part_size+1)
            print(young.partition_sequence, "was Franklin involuted to", young.updatePartitionSequence())
            young.updateLayers()
            young.updateDictionary()
            young.updateParts()
        elif diagonal_group.length <= bottom_group.length:
            # move diagonal group to bottom group
            landing_strip = VGroup()
            for dot in bottom_group:
                if dot.location[1] < diagonal_group.length:
                    landing_strip.add(dot)
            animations.append(ApplyMethod(diagonal_group.move_to, landing_strip.get_center() + young.RELATIVE_DOWN))
            for dot in diagonal_group:
                target_part_num = len(young.parts)-1
                target_part_size = (diagonal_group.length-1) - dot.location[0]
                animations.append(ApplyMethod(dot.move_to, young.coordinate_dictionary[(target_part_num, target_part_size)].get_center() + young.RELATIVE_DOWN))
                dot.location = (target_part_num + 1, target_part_size)
            for i in range(diagonal_group.length):
                young.partition_sequence[i] = young.partition_sequence[i]-1
            print(young.partition_sequence, "was Franklin involuted to", young.updatePartitionSequence())
            young.updateLayers()
            young.updateDictionary()
            young.updateParts()

        super().__init__(*animations)

class YoungTableauDemonstration(Scene):
    CONFIG = {
        "camera_config": {"background_color": "#181818"}
    }
    def construct(self):
        young_tableau = YoungTableau(partition_sequence=np.array([12,11,10,9,5,4]), shape="square", color="#46a0ee", center_x=-3, center_y=2).scale(.8)
        text = TextMobject("Franklin Involution").next_to(young_tableau, direction=UP, buff=SMALL_BUFF).scale(.5)
        young_tableau2 = YoungTableau(partition_sequence=np.array([7,6,5,3,1]), color="#8949d2", center_x=3, center_y=2)
        text2 = TextMobject("Conjugation").next_to(young_tableau2, direction=UP, buff=SMALL_BUFF).scale(.5)
        young_tableau3 = YoungTableau(partition_sequence=np.array([3,11,8,12,7,14]), color="#3ae9d5", center_x=-3, center_y=-2)
        text3 = TextMobject("Sorting Parts").next_to(young_tableau3, direction=UP, buff=SMALL_BUFF).scale(.5)
        young_tableau4 = YoungTableau(partition_sequence=np.array([8,7,5,5,3,1]), color="#e87335", center_x=3, center_y=-2)
        text4 = TextMobject("Convolution").next_to(young_tableau4, direction=UP, buff=SMALL_BUFF).scale(.5)
        # creation
        self.play(ShowCreation(young_tableau), ShowCreation(young_tableau2), ShowCreation(young_tableau3), ShowCreation(young_tableau4), ShowCreation(text), ShowCreation(text2),ShowCreation(text3), ShowCreation(text4))
        # animations
        self.play(FranklinInvoluting(young_tableau), Conjugating(young_tableau2), SortingParts(young_tableau3), Convoluting(young_tableau4))