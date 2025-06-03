// data/repositories/user_repo.dart
import 'package:cloud_firestore/cloud_firestore.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:geolocator/geolocator.dart';

import '../../core/utils/location_helper.dart';

import '../../core/app_constants.dart';
import '../models/user.dart' as app;

class UserRepository {
  final FirebaseFirestore _firestore;
  final FirebaseAuth _auth;

  UserRepository({
    FirebaseFirestore? firestore,
    FirebaseAuth? auth,
  })  : _firestore = firestore ?? FirebaseFirestore.instance,
        _auth = auth ?? FirebaseAuth.instance;

  app.User? get currentUser {
    final user = _auth.currentUser;
    if (user == null) return null;
    return app.User(
      id: user.uid,
      email: user.email ?? '',
      name: '',
      location: const GeoPoint(0, 0),
      contacts: '',
      lastUpdated: DateTime.now(),
    );
  }

  Future<void> updateUserLocation({
    required String userId,
    required double lat,
    required double lng,
  }) async {
    await _firestore.collection(AppConstants.usersCollection).doc(userId).update({
      AppConstants.locationField: GeoPoint(lat, lng),
      AppConstants.timestampField: FieldValue.serverTimestamp(),
    });
  }

  /// Получение потока ближайших пользователей
  Stream<List<app.User>> getNearbyUsersStream({
    required Position center,
    required double radius,
  }) {
    final bounds = _getGeoBounds(center.latitude, center.longitude, radius);

    return _firestore
        .collection(AppConstants.usersCollection)
        .where(
          AppConstants.locationField,
          isGreaterThan: bounds['min'],
          isLessThan: bounds['max'],
        )
        .snapshots()
        .map(
          (snapshot) => snapshot.docs
              .map((doc) => app.User.fromFirestore(doc))
              .where(
                (user) => LocationHelper.isWithinRadius(
                  centerLat: center.latitude,
                  centerLng: center.longitude,
                  targetLat: user.location.latitude,
                  targetLng: user.location.longitude,
                  radiusMeters: radius,
                ),
              )
              .toList(),
        );
  }

  /// Расчет границ для геозапроса
  Map<String, GeoPoint> _getGeoBounds(
    double lat,
    double lng,
    double radiusMeters,
  ) {
    const double distancePerDegree = 111000.0;
    final delta = radiusMeters / distancePerDegree;

    return {
      'min': GeoPoint(lat - delta, lng - delta),
      'max': GeoPoint(lat + delta, lng + delta),
    };
  }
}
